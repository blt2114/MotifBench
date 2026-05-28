import os
import numpy as np
import subprocess
import typing as T
import random
import shutil
import json
import logging
import glob
import math
import pandas as pd
from typing import Optional, Union, List, Tuple, Dict, Literal
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

import MDAnalysis as mda
import biotite
import biotite.structure.io as strucio
import biotite.structure as struc
import biotite.structure.io.pdb as pdb
import biotite.application.dssp as dssp
from biotite.structure.residues import get_residues
from biotite.structure import get_chains
from biotite.sequence import ProteinSequence
from biotite.sequence.io import fasta
from tmtools import tm_align
from Bio.PDB.parse_pdb_header import parse_pdb_header
from Bio.PDB import PDBParser
from pymol import cmd

log = logging.getLogger(__name__)

BACKBONE_ATOMS = {'N', 'CA', 'C', 'O', 'OXT'}

def reference_motif_extract(
    structure_path: Union[str, struc.AtomArray],
    atom_part: Optional[Literal["all-atom", "CA", "backbone"]] = "all-atom",
) -> struc.AtomArray:
    """Extracting motif from input protein structure.

    Args:
        structure_path (Union[str, None]): Input protein structure, can either be a path or an AtomArray.
        atom_part (str, optional): _description_. Defaults to "all".

    Returns:
        motif (biotite.structure.AtomArray): The motif positions extracted by user-specified way (all-atom / CA / backbone)
    """
    if isinstance(structure_path, str):
        array = strucio.load_structure(structure_path, model=1)
    else:
        array = structure_path
   
    # Get unique chain IDs
    chains = array.chain_id
    unique_chains = sorted(set(chains))
    
    result = []
    
    for chain in unique_chains:
        # Get all residues in the current chain
        residues_in_chain = array[array.chain_id == chain]
        residue_ids = residues_in_chain.res_id
        
        # Get the minimum and maximum residue IDs for this chain
        if len(residue_ids) > 0:
            min_res_id = min(residue_ids)
            max_res_id = max(residue_ids)
            
            if min_res_id == max_res_id:
                # If there's only one residue, just display the single residue
                result.append(f"{chain}{min_res_id}")
            else:
                # If there's a range, display it in the form chainX-Y
                result.append(f"{chain}{min_res_id}-{max_res_id}")
    
    # Join the results with slashes as required
    position = "/".join(result)

    return motif_extract(position, structure_path, atom_part)


def motif_extract(
    position: str,
    structure_path: Union[str, struc.AtomArray],
    atom_part: Optional[Literal["all-atom", "CA", "backbone"]] = "all-atom",
    split_char: str = "/"
) -> struc.AtomArray:
    """Extracting motif positions from input protein structure.

    Args:
        position (str): Motif region of input protein. DEMO: "A1-7/A28-79" corresponds defines res1-7 and res28-79 in chain A to be motif.
        structure_path (Union[str, None]): Input protein structure, can either be a path or an AtomArray.
        atom_part (str, optional): _description_. Defaults to "all".
        split_char (str): Spliting character between discontinuous motifs. Defaults to "/".

    Returns:
        motif (biotite.structure.AtomArray): The motif positions extracted by user-specified way (all-atom / CA / backbone)
    """

    position = position.split(split_char)
    if isinstance(structure_path, str):
        array = strucio.load_structure(structure_path, model=1)
    else:
        array = structure_path

    motif_array = []
    for i in position:
        chain_id = i[0]
        i = i.replace(chain_id, "")
        if "-" not in i: # Single-residue motif
            start = end = int(i)
        else:
            start, end = i.split("-")
            start, end = int(start), int(end)

        if atom_part == "all-atom":
            motif_array.append(array[(array.chain_id==chain_id) & (array.res_id <= end) & (array.res_id >= start) & (array.hetero==False)])
        elif atom_part == "CA":
            motif_array.append(array[(array.chain_id==chain_id) & (array.res_id <= end) & (array.res_id >= start) & (array.hetero==False) & (array.atom_name=="CA")])
        elif atom_part == "backbone":
            motif_array.append(array[(array.chain_id==chain_id) & (array.res_id <= end) & (array.res_id >= start) & (array.hetero==False) & ((array.atom_name=="N") | (array.atom_name=="CA")| (array.atom_name=="C") | (array.atom_name=="O"))])

    motif = motif_array[0]
    for i in range(len(motif_array) - 1):
        motif += motif_array[i + 1]
    return motif


def rmsd(
    reference: Union[str, struc.AtomArray],
    target: Union[str, struc.AtomArray],
) -> float:

    # Handle input protein type
    if isinstance(reference, str):
        reference = strucio.load_structure(reference, model=1)
    if isinstance(target, str):
        target = strucio.load_structure(target, model=1)

    mask_reference = (((reference.atom_name == "N") | (reference.atom_name == "CA") | (reference.atom_name == "C") | (reference.atom_name == "O")) & (biotite.structure.filter_amino_acids(reference)))
    reference = reference[mask_reference]
    mask_target = (((target.atom_name == "N") | (target.atom_name == "CA") | (target.atom_name == "C") | (target.atom_name == "O")) & (biotite.structure.filter_amino_acids(target)) )
    target = target[mask_target]
    superimposed, _ = struc.superimpose(reference, target)
    rms = struc.rmsd(reference, superimposed)
    return rms


def calculate_secondary_structure(
    input: Union[str, struc.AtomArray] = None,
) -> Optional[list]:
    """
    Calculate protein secondary structure.
    """
    array = strucio.load_structure(input)
    app = dssp.DsspApp(array)
    app.start()
    app.join()
    sse = app.get_sse()
    sse_format = "".join(sse)

    alpha_composition = (sse_format.count("H") + sse_format.count("G") + sse_format.count("I")) / len(sse_format) if len(sse_format) > 0 else 0
    beta_composition = (sse_format.count("B") + sse_format.count("E")) / len(sse_format) if len(sse_format) > 0 else 0
    coil_composition = (sse_format.count("C") + sse_format.count("S")) / len(sse_format) if len(sse_format) > 0 else 0
    turn_composition = sse_format.count("T") / len(sse_format) if len(sse_format) > 0 else 0

    return [sse_format, alpha_composition, beta_composition, coil_composition, turn_composition]


def radius_of_gyration(
    input: str,
    atom_part: Optional[str] = "all-atom",
    ) -> float:
    t = mda.Universe(input)
    if atom_part == 'all-atom':
        rg = t.atoms.radius_of_gyration()
    if atom_part == 'backbone':
        backbone = t.select_atoms("backbone")
        rg = backbone.atoms.radius_of_gyration()
    if atom_part == 'CA':
        c_alpha = t.select_atoms("name CA")
        rg = c_alpha.atoms.radius_of_gyration()
    return round(rg, 3)


def calc_tm_score(pos_1: np.ndarray, pos_2:np.ndarray, seq_1: str, seq_2: str) -> Tuple[float, float]:
    # Taken from FrameDiff codebase.
    tm_results = tm_align(pos_1, pos_2, seq_1, seq_2)
    return tm_results.tm_norm_chain1, tm_results.tm_norm_chain2


def calc_aligned_rmsd(pos_1: np.ndarray, pos_2: np.ndarray) -> Union[int, float]:
    # Adapted from FrameDiff codebase.
    # https://github.com/jasonkyuyim/se3_diffusion/blob/53359d71cfabc819ffaa571abd2cef736c871a5d/analysis/metrics.py#L71-L73
    # Note this implementation differs from FrameDiff that
    # FrameDiff calculates the mean RMSD over all residues of $\frac{1}{N} {\sum_{i=1}^N \parallel \vec{x_i} - \vec{y_i} \parallel_2}$
    # While we follow the standard RMSD computation of $\sqrt{\frac{1}{N} \sum_{i=1}^N \parallel \vec{x_i} - \vec{y_i} \parallel_2^2}$
    # Both performs rigid transform using Kabsch algorithm before computing RMSD.
    aligned_pos_1 = rigid_transform_3D(pos_1, pos_2)[0]
    return np.sqrt(np.mean(np.linalg.norm(aligned_pos_1 - pos_2, axis=-1) ** 2))


def rigid_transform_3D(A:np.ndarray, B:np.ndarray, verbose: bool=False) -> Tuple:
    # Transforms A to look like B
    # https://github.com/nghiaho12/rigid_transform_3D
    assert A.shape == B.shape
    A = A.T
    B = B.T

    num_rows, num_cols = A.shape
    if num_rows != 3:
        raise Exception(f"matrix A is not 3xN, it is {num_rows}x{num_cols}")

    num_rows, num_cols = B.shape
    if num_rows != 3:
        raise Exception(f"matrix B is not 3xN, it is {num_rows}x{num_cols}")

    # find mean column wise
    centroid_A = np.mean(A, axis=1)
    centroid_B = np.mean(B, axis=1)

    # ensure centroids are 3x1
    centroid_A = centroid_A.reshape(-1, 1)
    centroid_B = centroid_B.reshape(-1, 1)

    # subtract mean
    Am = A - centroid_A
    Bm = B - centroid_B

    H = Am @ np.transpose(Bm)

    # sanity check
    #if linalg.matrix_rank(H) < 3:
    #    raise ValueError("rank of H = {}, expecting 3".format(linalg.matrix_rank(H)))

    # find rotation
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T

    # special reflection case
    reflection_detected = False
    if np.linalg.det(R) < 0:
        if verbose:
            print("det(R) < R, reflection detected!, correcting for it ...")
        Vt[2,:] *= -1
        R = Vt.T @ U.T
        reflection_detected = True

    t = -R @ centroid_A + centroid_B
    optimal_A = R @ A + t

    return optimal_A.T, R, t, reflection_detected


def parse_pdb_feats(
        pdb_name: str,
        pdb_path: str,
        scale_factor: Union[str, float] = 1.,
        chain_id: str = 'A',
    ):
    """
    Taken from FrameDiff codebase.
    Only used in inference procedure to prepare ESMFold prediction.

    Args:
        pdb_name: name of PDB to parse.
        pdb_path: path to PDB file to read.
        scale_factor: factor to scale atom positions.
        mean_center: whether to mean center atom positions.
    Returns:
        Dict with CHAIN_FEATS features extracted from PDB with specified
        preprocessing.
    """
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure(pdb_name, pdb_path)
    struct_chains = {
        chain.id: chain
        for chain in structure.get_chains()}

    def _process_chain_id(x):
        chain_prot = process_chain(struct_chains[x], x)
        chain_dict = dataclasses.asdict(chain_prot)

        # Process features
        feat_dict = {x: chain_dict[x] for x in CHAIN_FEATS}
        return parse_chain_feats(
            feat_dict, scale_factor=scale_factor)

    if isinstance(chain_id, str):
        return _process_chain_id(chain_id)
    elif isinstance(chain_id, list):
        return {
            x: _process_chain_id(x) for x in chain_id
        }
    elif chain_id is None:
        return {
            x: _process_chain_id(x) for x in struct_chains
        }
    else:
        raise ValueError(f'Unrecognized chain list {chain_id}')


def randomly_select_and_copy_pdb_files(
    src_folder: Union[str, Path],
    dst_folder: Union[str, Path], 
    num_files: int) -> None:
    """
    Randomly select and copy a specified number of PDB files
    from a source folder to a destination folder.

    src_folder: Path to the source folder containing PDB files.
    dst_folder: Path to the destination folder where files will be copied.
    num_files: Number of PDB files to randomly select and copy.
    """
    # Get a list of all PDB files in the source folder
    pdb_files = [file for file in os.listdir(src_folder) if file.endswith('.pdb')]

    # Check if the source folder has enough files
    if len(pdb_files) < num_files:
        raise ValueError(f"Source folder has only {len(pdb_files)} files, but {num_files} files are requested.")

    # Randomly select the specified number of PDB files
    selected_files = random.sample(pdb_files, num_files)

    # Create the destination folder if it doesn't exist
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    # Copy each selected file to the destination folder
    for file in selected_files:
        shutil.copy(os.path.join(src_folder, file), os.path.join(dst_folder, file))


def cleanup_af2_outputs(
    raw_dir: Union[str, Path],
    clean_dir: Union[str, Path],
    remove_after_cleanup: bool = False
) -> Dict:

    output_dict = {}
    for file in os.listdir(raw_dir):
        if file.endswith('.pdb'):
            if file.startswith('T_0') == False: # original backbone sequence
                new_path = os.path.join(clean_dir, 'sample_0.pdb')
                shutil.copy2(os.path.join(raw_dir, file), new_path)
                output_dict['sample_0'] = {}
                output_dict['sample_0']['sample_path'] = os.path.abspath(new_path)
            else: # Designed sequence
                sample_index = os.path.splitext(file)[0].split('sample_')[1].split('__score')[0]
                new_path = os.path.join(clean_dir, f'sample_{sample_index}.pdb')
                shutil.copy2(os.path.join(raw_dir, file), new_path)
                if f'sample_{sample_index}' not in output_dict:
                    output_dict[f'sample_{sample_index}'] = {}
                output_dict[f'sample_{sample_index}']['sample_path'] = os.path.abspath(new_path)
        elif file.endswith('.json') and 'rank' in file: # file storing pLDDT & pTM & pAE
            if file.startswith('T_0'):
                sample_index = os.path.splitext(file)[0].split('sample_')[1].split('__score')[0]
                if f'sample_{sample_index}' not in output_dict:
                    output_dict[f'sample_{sample_index}'] = {}
                with open(os.path.join(raw_dir, file), 'r') as f:
                    j = json.load(f)
                    output_dict[f'sample_{sample_index}']['plddt'] = np.mean(j['plddt'])
                    output_dict[f'sample_{sample_index}']['pae'] = np.mean(j['pae'])
                    output_dict[f'sample_{sample_index}']['ptm'] = np.mean(j['ptm'])
            else: # original backbone sequence
                if 'sample_0' not in output_dict:
                    output_dict['sample_0'] = {}
                with open(os.path.join(raw_dir, file), 'r') as f:
                    j = json.load(f)
                    output_dict['sample_0']['plddt'] = np.mean(j['plddt'])
                    output_dict['sample_0']['pae'] = np.mean(j['pae'])
                    output_dict['sample_0']['ptm'] = np.mean(j['ptm'])
    if remove_after_cleanup:
        shutil.rmtree(raw_dir, ignore_errors=True)
    return output_dict


def write_seqs_to_fasta(
    input_seqs: Union[Dict, list, str],
    fasta_path: Union[str, Path]
) -> None:
    fasta_instance = fasta.FastaFile()
    for header, string in input_seqs.items():
        fasta_instance[header] = string
    fasta_instance.write(fasta_path)


def reference_contig_from_segments(pdb_file: Union[str, Path], segment_order: str):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("structure", pdb_file)
    
    chain_ranges = []
    
    # Split the chain_order string into a list of chain identifiers
    chains = segment_order.split(";")
    
    for chain_id in chains:
        chain = structure[0][chain_id]
        residues = list(chain.get_residues())
        
        # Find the range of residue numbers in the chain
        if residues:
            start_res = residues[0].get_id()[1]  # Start residue number
            end_res = residues[-1].get_id()[1]   # End residue number
            chain_ranges.append(f"{chain_id}{start_res}-{end_res}")
    
    # Join all chain ranges with "/" separator
    return "/".join(chain_ranges)


def get_csv_data(
    csv_info: Union[str, Path],
    pdb_name: str,
    sample_num: Union[str, int],
    save_csv: Optional[Union[str, Path]] = None
) -> Tuple:
    """Index information from input csv file.

    Args:
        csv_info (Union[str, Path]): CSV file containing motif information. (Template: ./demo/motif_scaffolding/motif_info.csv)
        pdb_name (str): The name of sampled PDB file with format {pdb_name}_{sample_num}.pdb. e.g. 2KL8_33.pdb -> 2KL8
        sample_num (Union[str, int]): Number of samples with format {pdb_name}_{sample_num}.pdb. e.g. 2KL8_33.pdb -> 33

    Returns:
        Tuple: A tuple containing information from each column.
            contig (str): Motif and scaffold information, where motifs start with characters and scaffolds start with numbers.
            mask (str): 1D boolean array containing motif positions. True -> motif, False -> scaffold
            motif_indices (str): List containing motif positions
            redesign_positions (str): Positions to be redesigned, segmented by ';'
    """
    csv_info = pd.read_csv(csv_info)
    csv_info['sample_num'] = csv_info['sample_num'].astype(int)
    sample_item = csv_info[(csv_info['pdb_name'] == pdb_name) & (csv_info['sample_num'] == int(sample_num))]
    if not sample_item.empty:
        contig = sample_item['contig'].iloc[0]
        segments_order = sample_item['segment_order'].iloc[0]
        length, motif_indices, motif_mask = generate_indices_and_mask(contig)
        if 'motif_indices' not in csv_info.columns:
            csv_info['motif_indices'] = None
        if 'mask' not in csv_info.columns:
            csv_info['mask'] = None

        csv_info.at[sample_item.index[0], 'motif_indices'] = motif_indices
        csv_info.at[sample_item.index[0], 'mask'] = motif_mask

        return(
            sample_item['contig'].iloc[0],
            motif_mask,
            motif_indices,
            sample_item['redesign_positions'].iloc[0] if 'redesign_positions' in sample_item.columns and not pd.isna(sample_item['redesign_positions'].iloc[0]) else "",
            segments_order
        )


def motif_indices_to_contig(motif_indices: Union[List, str]) -> str:
    """Extract motif contig from overall contig.
    e.g. "A1-7/20-20/A28-79" -> "A1-7/A28-79"
    TBD: Support multiple chains beyond chain A.

    Args:
        motif_indices (str): The str object of motif list from "motif_indices" returned by `get_csv_data()`.

    Returns:
        contig: Contig containing motif information.
    """
    if isinstance(motif_indices, list):
        motif_indices = motif_indices
    elif isinstance(motif_indices, str) and motif_indices.startswith('[') and motif_indices.endswith(']'):
        motif_indices = motif_indices.strip('[]').split(', ')
        try:
            motif_indices = [int(index) for index in motif_indices]
        except ValueError as e:
            raise ValueError(f"Error converting motif_indices_str to list of integers: {e}")
    else:
        raise ValueError(f"Invalid input for motif_indices_to_contig: {motif_indices}")

    sorted_indices = sorted(motif_indices)
    contig = ""
    range_start = None

    for i, index in enumerate(sorted_indices):
        if range_start is None:
            range_start = index
        if i == len(sorted_indices) - 1 or sorted_indices[i + 1] != index + 1:
            if contig:
                contig += "/"
            if range_start == index:
                contig += f"A{range_start}"
            else:
                contig += f"A{range_start}-{index}"
            range_start = None
    return contig


def motif_indices_to_fixed_positions(motif_indices: Union[str, List]) -> str:
    """Converts motif indices to the fixed positions string format compatible with ProteinMPNN.
    e.g. [1, 2, 3, 4, 5, 8, 9] -> "1 2 3 4 5 8 9"

    Args:
        motif_indices (Union[str, List]): List-like motif indices.

    Returns:
        fix_positions (str): A str containing fixed positions seperated by space.
    """
    # Converts motif indices to the fixed positions string format
    if isinstance(motif_indices, list):
        motif_indices = str(motif_indices)
    motif_indices = motif_indices.strip('[]').split(', ')
    motif_indices = sorted([int(index) for index in motif_indices])
    fixed_positions = ' '.join(str(idx) for idx in motif_indices)
    return f"{fixed_positions}"


def parse_contig_string(
    contig_string: str,
    split_char: str="/"
    ) -> List:
    # Code by @blt2114
    contig_segments = []
    for motif_segment in contig_string.split(split_char):
        segment_dict ={"chain":motif_segment[0]}
        if "-" in motif_segment:
            segment_dict["start"], segment_dict["end"] = motif_segment[1:].split("-")
        else:
            segment_dict["start"] = segment_dict["end"] = motif_segment[1:]
        contig_segments.append(segment_dict)
    return contig_segments


def introduce_redesign_positions(
    fix_positions: Union[List, str],
    redesign_positions: str
) -> List:
    """Adjust fixed positions list to make certain positions redesignable.

    Args:
        fix_positions (Union[List, str]): Fixed positions
        redesign_positions (str): Redesigned list from "redesign_positions" returned by `get_csv_data()`.

    Returns:
        List: A list of fixed positions for ProteinMPNN, laterly as input for `motif_indices_to_fixed_positions`.
    """
    if isinstance(fix_positions, list):
        fix_positions = str(fix_positions)

    pos_to_redesign = parse_contig_string(redesign_positions)
    redesign_pos = []
    for seg in pos_to_redesign:
        for i in range(int(seg['start']), int(seg['end']) + 1):
            redesign_pos.append(int(i))
    final_pos = [pos for pos in eval(fix_positions) if pos not in redesign_pos]
    return final_pos


def generate_indices_and_mask(contig: str) -> Tuple[int, List[int], np.ndarray]:
    """Index motif and scaffold positions by contig for sequence redesign.
    Args:
        contig (str): A string containing positions for scaffolds and motifs.

        Details:
        Scaffold parts: Contain a single integer.
        Motif parts: Start with a letter (chain ID) and contain either a single positions (e.g. A33) or a range of positions (e.g. A33-39).
        The numbers following chain IDs corresponds to the motif positions in native backbones, which are used to calculate motif reconstruction later on.
        e.g. "15/A45-65/20/A20-30"
        NOTE: The scaffold part should be DETERMINISTIC in this case as it contains information for the corresponding protein backbones.

    Raises:
        ValueError: Once a "-" is detected in scaffold parts, throws an error for the aforementioned reason.

    Returns:
        A Tuple containing:
            - overall_length (int): Total length of the sequence defined by the contig.
            - motif_indices (List[int]): List of indices where motifs are located.
            - motif_mask (np.ndarray): Boolean array where True indicates motif positions and False for scaffold positions.
    """
    ALPHABET = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    components = contig.split('/')
    current_position = 1  # Start positions at 1 for 1-based indexing
    motif_indices = []
    motif_mask = []

    for part in components:
        if part[0] in ALPHABET:
            # Motif part
            if '-' in part:
                start, end = map(int, part[1:].split("-"))
            else: # Single motif
                start = end = int(part[1:])
            length = (end - start + 1)
            motif_indices.extend(range(current_position, current_position + length))
            motif_mask.extend([True] * length)
        else:
            # Scaffold part
            if '-' in part:
                assert part.split('-')[0] == part.split('-')[-1]
                length = int(part.split('-')[0])
                #raise ValueError(f'There is "-" in scaffold {part}, which supposed to be determined already! Please check again.')
            else:
                length = int(part)
            motif_mask.extend([False] * length)

        current_position += length  # Update the current position after processing each part

    # Convert motif_mask to a numpy array for more efficient boolean operations
    motif_mask = np.array(motif_mask, dtype=bool)
    overall_length = motif_mask.shape[0]

    return (overall_length, motif_indices, motif_mask)


def get_redesign_positions(pdb_path: Union[str, Path]) -> Tuple[List[int], List[str], str]:
    """Index residues to be redesigned by "UNK" residues.

    Args:
        pdb_path (Union[str, Path]): File path for input PDB file.

    Returns:
        Information for redesign positions
          redesign_positions (List[int]): Indices of positions to be redesigned inside biotite array object.
          redesign_chain_pos (List[str]): Indices integrated with chain information. Useful for further information storing.
    """
    all_atom_array = strucio.load_structure(pdb_path)
    ca_array = all_atom_array[(all_atom_array.atom_name == "CA")] # Get C-alpha array for convenience of indexing

    # Get three lists to iterate
    res_id_list = ca_array.res_id
    chain_id_list = ca_array.chain_id
    res_name_list = ca_array.res_name

    if 'UNK' in res_name_list:
        redesign_positions = [index for index, resname in zip(res_id_list, res_name_list) if resname == "UNK"]
        redesign_chain_positions = [f"{chain_id_list[idx]}{res_id_list[idx]}" for idx, resname in enumerate(res_name_list) if resname == "UNK"]

        formatted_chain_positions = format_chain_positions(redesign_chain_positions)

        return(redesign_positions, redesign_chain_positions, formatted_chain_positions)

    else:
        return None


def read_contig_from_header(pdb_path: Union[str, Path]) -> Optional[Tuple[str, str]]:
    """Read contig information from HEADER record of PDB file.
    By default, the contig info is stored at the "classification" section and
    file name is stored at the "identifier" section.

    Args:
        pdb_path (Union[str, Path]): Path of input PDB file.

    Returns:
        contig (str): The contig information for where motifs and scaffolds are placed.
        identifier (str): The file name of input PDB file.

        If HEADER couldn't be parsed, then it's either because problem in format or
        you use csv instead of HEADER to load contig information. Return nothing in this case.
    """
    try:
        header_info = parse_pdb_header(pdb_path)
        contig = header_info['head'].upper().split(' ')[0]
        file_identifier = header_info['idcode']
        return contig, file_identifier
    except KeyError as e:
        logging.warning(f"The HEADER of {pdb_path} could not be parsed properly. Please make sure the format is right\
            or you are using csv file to provide information for contig.")
        return None


def write_contig_into_header(
    pdb_path: Union[str, Path],
    contig: str,
    output_path: Optional[Union[str, Path]],
    write_additional_info: bool = True,
    ) -> None:

    date = datetime.now().strftime("%d-%b-%y").upper() if write_additional_info else ""
    #identifier = os.path.basename(pdb_path).strip('.pdb') if write_additional_info else ""
    header_string = f"HEADER    {contig:<40}{date:>9}\n"
    save_path = output_path if output_path is not None else pdb_path

    with open(pdb_path, "r") as f:
        file_lines = f.readlines()
        file_lines.insert(0, header_string)
    with open(save_path, "w") as f:
        f.writelines(file_lines)


def csv_merge(
    root_dir: Union[str, Path],
    prefix: str = "esm",
    ) -> Tuple[pd.DataFrame, int]:
    """
    Merge evaluation results from different backbones into a single Dataframe file.

    Args:
        root_dir (Union[str, Path]): Root directory to search evaluation
            results.  Should be the ".../evals/" dir with paths
            format e.g. ".../evals/00_1BCF_1/self_consistency/esm_eval_results.csv"
        prefix (str): Prefix to merge files. Default = 'esm', alternative = 'af2' or 'joint'.

    Returns:
        A tuple object containing:
            1. The merged dataframe containing all evaluation results for one input folder.
            2. The count of files included in the input folder. Useful when calculating proportion of designability or novelty.
    """
    if prefix not in ['esm', 'af2', 'joint']:
        raise ValueError("Prefix must be 'esm', 'af2' or 'joint'!")

    merged_data = pd.DataFrame()
    log.info(f'Merging evaluation results from {root_dir}......')
    file_count = 0
    for root, dirs, files in os.walk(root_dir, followlinks=True):
        for file in files:
            if file == f'{prefix}_eval_results.csv':
                file_count += 1
                csv_path = os.path.join(root, file)
                df = pd.read_csv(csv_path)

                parent_dir = os.path.abspath(os.path.join(root, os.pardir))
                #print(parent_dir)
                pdb_files = glob.glob(os.path.join(parent_dir, '*.pdb'))

                # Check if there is more than one .pdb file
                if len(pdb_files) > 1:
                    raise RuntimeError(f"More than one .pdb file found in {parent_dir}")
                elif pdb_files:
                    df['backbone_path'] = os.path.abspath(pdb_files[0])
                else:
                    df['backbone_path'] = None

                if prefix == 'esm':
                    df['folding_method'] = 'ESMFold'
                elif prefix == 'af2':
                    df['folding_method'] = 'AlphaFold2'

                merged_data = pd.concat([merged_data, df], ignore_index=True)

    log.info(f'Collected evaluation results from {file_count} protein backbones.')

    return merged_data, file_count


def read_folding_method(
    eval_data: Union[str, Path, pd.DataFrame],
    prefix: str = 'esm',
    ) -> Dict:
    eval_results = pd.read_csv(eval_data) if isinstance(eval_data, str) or isinstance(eval_data, Path) else eval_data
    
    if prefix == 'esm' or prefix == 'af2':
        return eval_results
    elif prefix == 'joint':
        esm_data = eval_results["folding_method"] == "ESMFold"
        af2_data = eval_results["folding_method"] == "AlphaFold2"
        return {'esm': esm_data, 'af2': af2_data}
        

def analyze_success_rate(
        merged_data: Union[str, Path, pd.DataFrame], 
        group_mode: str = "all",
        prefix: str = "esm"
    ):

    # Define success criteria for each sample
    merged_data = pd.read_csv(merged_data) if isinstance(merged_data, str) or isinstance(merged_data, Path) else merged_data

    #merged_data['backbone_success'] = (merged_data['rmsd'] < 2)
    #merged_data['motif_success'] = (merged_data['motif_rmsd'] < 1)


    merged_data['seq_hit'] = (merged_data['rmsd'] < 2) & (merged_data['motif_rmsd'] < 1)
    merged_data['seq_backbone_hit'] = (merged_data['rmsd'] < 2)
    merged_data['seq_motif_hit'] = (merged_data['motif_rmsd'] < 1)

    #merged_data['all_success'] = merged_data['motif_success'] & merged_data['backbone_success']
    # Group by 'backbone_path' and aggregate the success criteria
    group_success = merged_data.groupby('backbone_path').agg({
        'seq_hit': 'any',
        'seq_backbone_hit': 'any',
        'seq_motif_hit': 'any'
    }).rename(columns={
        'seq_hit': 'Success',
        'seq_backbone_hit': 'backbone_success',
        'seq_motif_hit': 'motif_success'
    })

    # Join the aggregated results back to the original DataFrame
    merged_data = merged_data.merge(group_success, on='backbone_path', how='left')

    successful_backbones = set()
    if group_mode == 'all':
        success_count = merged_data[merged_data['Success'] == True]['backbone_path'].nunique()
        successful_backbones = set(merged_data[merged_data['Success'] == True]['backbone_path'])
    elif group_mode == 'PDB id':
        success_count = dict.fromkeys(merged_data['PDB id'].unique(), 0)
        success_per_pdb = merged_data[merged_data['Success'] == True].groupby('PDB id')['backbone_path'].nunique()
        success_count.update(success_per_pdb.to_dict())
        successful_backbones = set(merged_data[merged_data['Success'] == True]['backbone_path'])

    #print(f'merged_data.columns: {set(merged_data.columns)}')

    summary_data = merged_data.drop(columns=["header", "refold_motif_rmsd", "ptm", "pae",
    "plddt", "folding_method", "backbone_success", "motif_success", "seq_backbone_hit", "seq_motif_hit",
    "backbone_motif_rmsd", "mpnn_score", "tm_score"], inplace=False)
    #print(f'summary_data.columns: {set(summary_data.columns)}\nmerged_data.columns: {set(merged_data.columns)}\n')

    # Find closest contender
    designable_scaffolds = merged_data[merged_data["rmsd"] < 2.0]
    if not designable_scaffolds.empty:
        closest_contender = designable_scaffolds.loc[designable_scaffolds["motif_rmsd"].idxmin()]
        closest_contender_df = closest_contender.to_frame().T
    else:
        closest_contender = None
        closest_contender_df = None

    return merged_data, summary_data, success_count, successful_backbones, closest_contender_df


def _process_results(self, prefix: str):
    """Process results for a single folding method."""
    results_df, pdb_count = csv_merge(root_dir=self._result_dir, prefix=prefix)

    # Analyze outputs
    complete_results, summary_results, designability_count, backbones = analyze_success_rate(
        merged_data=results_df, group_mode="all", prefix=prefix
    )

    summary_csv_path = os.path.join(self._result_dir, f"{prefix}_summary_results.csv")
    complete_csv_path = os.path.join(self._result_dir, f"{prefix}_complete_results.csv")
    complete_results.to_csv(complete_csv_path, index=False)
    summary_column_order = [
        "sample_idx",
        "Success",
        "rmsd",
        "motif_rmsd",
        "length",
        "sequence",
        "sample_path",
        "backbone_path",
    ]
    summary_results.to_csv(summary_csv_path, columns=summary_column_order, index=False)

    return complete_results, backbones, designability_count, pdb_count


def format_chain_positions(positions: List[str]) -> str:
    if not positions:
        return ""

    formatted_positions = []
    current_chain = positions[0][0]
    start_num = int(positions[0][1:])
    end_num = start_num

    for pos in positions[1:]:
        chain, num = pos[0], int(pos[1:])
        if chain == current_chain and num == end_num + 1:
            end_num = num
        else:
            if start_num == end_num:
                formatted_positions.append(f"{current_chain}{start_num}")
            else:
                formatted_positions.append(f"{current_chain}{start_num}-{end_num}")
            current_chain = chain
            start_num = end_num = num

    # Append the last range or number
    if start_num == end_num:
        formatted_positions.append(f"{current_chain}{start_num}")
    else:
        formatted_positions.append(f"{current_chain}{start_num}-{end_num}")

    return ";".join(formatted_positions)


def parse_input_scaffold(
    pdb_path: Union[str, Path],
    #benchmark_csv: Union[str, Path, pd.DataFrame]
):
    """Parse information based on input contig.
    # Example contig: "2KL8,A1-7/20/A28-79,A3-5;A33;A36"

    """
    contig = read_contig_from_header(pdb_path)[0] # Example contig
    if len(contig.split(',')) == 3:
        pdb_id, motif_spec, redesign_idx = contig.split(',')
    elif len(contig.split(',')) == 2:
        pdb_id, motif_spec = contig.split(',')
        if get_redesign_positions(pdb_path) is not None:
            redesign_idx = get_redesign_positions(pdb_path)[2]
    else:
        raise ValueError(f'Incorrect format for contig {contig}! Please check again.')

    #native_motif = benchmark_csv.iloc[pdb_id][0][1] # Need to be changed, structure of input motif
    design_motif = motif_extract(motif_spec, pdb_path, atom_part='backbone') # structure of designed motif

    # "A1-7/20/A28-79" ->
      # length: 79
      # motif_indices: [1, 2, ..., 7, 28, ..., 78, 79]
      # motif_mask: [True, True, ..., False, ..., True]
    length, motif_indices, motif_mask = generate_indices_and_mask(motif_spec)
    # Get redesigned positions from native motifs by 'UNK'
    #native_redesign_idx = get_redesign_positions(native_motif)
    # Make sure don't cheat
    #assert len() == len(parse_contig_string)
    #design_contig = motif_indices_to_contig(motif_spec) # "A1-7/20/A28-79" -> "A1-7/A28-79"

    # Introduce positions to be redesigned and turn into format compatible with ProteinMPNN
    #fix_positions = motif_indices_to_fixed_positions(motif_indices) # [1, 2, 3, ...., 79] -> [1 2 3 ... 79]
    #if redesign_idx:
    #    fix_positions = introduce_redesign_positions(fix_positions, redesign_idx) # [1 2 3 ..., 79] -> [1 2 ... 79]
    return (
        motif_spec,
        motif_mask,
        motif_indices,
        redesign_idx,
        #native_motif,
        #design_motif
    )


def write_summary_results(
    stored_path: Union[str, Path],
    pdb_count: Union[int, float],
    designable_count: Union[int, float],
    diversity_result: Union[Dict, int, float],
    novelty_value: Union[int, float, str],
    prefix: Optional[str] = None
) -> None:

    designable_fraction = f'{(designable_count / (pdb_count + 1e-6) * 100):.2f}'
    number_of_solutions = f'{diversity_result["Clusters"]}'
    novelty_value = round(novelty_value, 3)
    novelty_value = f'{novelty_value:.3f}' if isinstance(novelty_value, (int or float)) else novelty_value

    # Formatting
    summary_table = [
        ["Evaluated Protein", os.path.basename(os.path.normpath(stored_path))],
        ["Number of Unique Solutions (Unique designable scaffolds)", number_of_solutions],
        ["Novelty (Weighted across each cluster)", novelty_value],
        ["Success Rate", f"{designable_fraction}%"],
        ["Number of Scaffolds Evaluated", f"{pdb_count}"]
    ]
    formatted_table = tabulate(summary_table, tablefmt="grid", numalign="center")

    with open (os.path.join(stored_path, f'{prefix}_summary.txt'), 'w') as f:
        f.write('----------Summary----------\n\n')
        f.write(f'The following are evaluation results for {os.path.abspath(stored_path)}:\n\n')
        f.write(formatted_table + "\n")
        #f.write(f'Evaluated protein: {os.path.basename(os.path.normpath(stored_path))}\n')
        #f.write(f'Number of unique solutions (Unique designable scaffolds): {number_of_solutions}\n')
        #f.write(f'Novelty (Weighted across each cluster): {novelty_value}\n')
        #f.write(f'Success rate: {designable_fraction}%\n')


def write_auxiliary_metrics(
    stored_path: Union[str, Path],
    auxiliary_results: Optional[Union[str, Path, pd.DataFrame]] = None,
    prefix: Optional[str] = None
) -> None:

    if not auxiliary_results is None:
        closest_motif_rmsd = auxiliary_results['motif_rmsd'].iloc[0]
        closest_contender_designability = auxiliary_results['rmsd'].iloc[0]
        closest_contender_scaffold = auxiliary_results['backbone_path'].iloc[0]
        closest_contender_refold = auxiliary_results['sample_path'].iloc[0]
    else:
        closest_motif_rmsd = "\\"
        closest_contender_designability = "\\"
        closest_contender_scaffold = "\\"
        closest_contender_refold = "\\"

    # Formatting
    summary_table = [
        ["Evaluated Protein", os.path.basename(os.path.normpath(stored_path))],
        ["Closest Contender (Scaffold)", closest_contender_scaffold],
        ["Closest Contender (Refolded Structure)", closest_contender_refold],
        ["Closest Motif-RMSD (Å)", closest_motif_rmsd],
        ["Scaffold RMSD of Closest Contender (Å)", closest_contender_designability],
    ]
    formatted_table = tabulate(summary_table, tablefmt="grid", numalign="center")

    with open (os.path.join(stored_path, f'{prefix}_auxiliary_metrics.txt'), 'w') as f:
        f.write('----------Auxiliary Metrics----------\n\n')
        f.write(f'The following are auxiliary metrics for {os.path.abspath(stored_path)}:\n\n')
        f.write(formatted_table + "\n")


def parse_contig(contig: str) -> List[Tuple[str, int, int]]:
    """
    Parse contig into a list of tuples with (chain, start, end) or ("scaffold", scaffold_length).
    """
    segments = []
    for part in contig.split("/"):
        if part[0].isalpha():  # Motif segment
            chain = part[0]
            if "-" in part[1:] and len(part[1:].split("-")) == 2:
                start, end = map(int, part[1:].split("-"))
                segments.append((chain, start, end))
            else:
                start = end = int(part[1:])
                segments.append((chain, start, end))
        else:  # Scaffold segment
            if len(part.split("-")) == 2:
                scaffold_length = int(part.split("-")[0])
            else:
                scaffold_length = int(part)
            segments.append(("scaffold", scaffold_length))  # No chain for scaffold
    return segments


def parse_redesign_positions(positions: str) -> List[Tuple[str, int, int]]:
    """
    Parse redesign positions into a list of tuples (chain, start, end).
    Handles both single positions (e.g., 'A18') and ranges (e.g., 'A19-20').
    """
    parsed_positions = []
    if len(positions) == 0: return parsed_positions
    for pos in positions.split(";"):
        chain = pos[0]
        if "-" in pos:
            start, end = map(int, pos[1:].split("-"))
            parsed_positions.append((chain, start, end))
        else:  # Single position like 'A18'
            start = end = int(pos[1:])
            parsed_positions.append((chain, start, end))
    return parsed_positions


def get_non_redesign_positions(contig_segments: List[Tuple[Union[str, None], int, int]], redesign_segments: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
    """
    Determine non-redesign positions by subtracting redesign segments from contig segments.
    """
    non_redesign_positions = []

    for segment in contig_segments:
        if segment[0] == "scaffold":
            continue  # Skip scaffold segments

        chain, start, end = segment
        current_pos = start

        while current_pos <= end:
            # Check if this position is within any redesign segment
            is_redesign = any(chain == r_chain and r_start <= current_pos <= r_end for r_chain, r_start, r_end in redesign_segments)
            if not is_redesign:
                non_redesign_positions.append((chain, current_pos))
            current_pos += 1

    return non_redesign_positions


def check_motif_positions(
    motif_pdb_path: Union[str, Path],
    reference_contig: str,
    segment_order: str,
    redesign_positions: str,
    ) -> None:
    # Parse contig and redesign positions
    contig_segments = parse_contig(reference_contig)
    redesign_segments = parse_redesign_positions(redesign_positions) 
    segment_order_list = segment_order.split(";")

    # Build a mapping of segment names (A, B, etc.) to contig segments
    motif_mapping = {}
    motif_index = 0  # Index for tracking motif segments

    for segment in contig_segments:
        if segment[0] != "scaffold":  # Motif segment
            chain, start, end = segment
            segment_name = segment_order_list[motif_index]
            motif_mapping[segment_name] = (chain, start, end)
            motif_index += 1

    # Load motif PDB using biotite
    pdb_array = strucio.load_structure(motif_pdb_path)
    ca_atoms = pdb_array[pdb_array.atom_name == "CA"]  # Select only CA atoms

    # Check redesign positions
    for chain, start, end in redesign_segments:
        for segment_name, (motif_chain, motif_start, motif_end) in motif_mapping.items():
            if chain == motif_chain and motif_start <= start <= motif_end:
                relative_start = start - motif_start + 1
                relative_end = end - motif_start + 1
                motif_chain_atoms = ca_atoms[ca_atoms.chain_id == segment_name]

                for i in range(relative_start, relative_end + 1):
                    residue = motif_chain_atoms[motif_chain_atoms.res_id == i]
                    if len(residue) == 0:
                        log.warning(f"Residue {segment_name}{i} not found in motif PDB file {os.path.basename(motif_pdb_path)}.")
                    elif residue[0].res_name != "UNK":
                        log.warning(f"Residue {segment_name}{i} in {os.path.basename(motif_pdb_path)} is not 'UNK' but '{residue[0].res_name}'. This is not allowed to be redesigned.")

                print(f"Redesign positions {chain}{start}-{end} correctly marked as 'UNK' in chain {segment_name} of {os.path.basename(motif_pdb_path)}.")

    # Check whether positions not allowed to be redesigned contained within the provided list of redesign positions 
    # i.e. The complementary set of {motif_positions} and {redesign_positions}
    non_redesign_segments = get_non_redesign_positions(contig_segments, redesign_segments)
    for chain, pos in non_redesign_segments:
        for segment_name, (motif_chain, motif_start, motif_end) in motif_mapping.items():
            if chain == motif_chain and motif_start <= pos <= motif_end:
                relative_pos = pos - motif_start + 1
                motif_chain_atoms = ca_atoms[ca_atoms.chain_id == segment_name]

                residue = motif_chain_atoms[motif_chain_atoms.res_id == relative_pos]
                if len(residue) == 0:
                    log.warning(f"Residue {segment_name}{relative_pos} not found in motif PDB.")
                elif residue[0].res_name == "UNK":
                    log.warning(f"Residue {segment_name}{relative_pos} should not be 'UNK'. Found 'UNK'.")

                print(f"Non-redesign position {chain}{pos} correctly marked in chain {segment_name}.")

    print("All redesign and non-redesign positions are correctly verified.")


# -------------------- Utils for redesign positions parsing -----------------------#
def parse_contig_to_dict(contig_string: str) -> List[Dict[str, Union[str, int]]]:
    """
    Parse a contig-like string (e.g., "10/A92-99/15") into a list of dictionaries.
    Each dictionary has the chain, start, and end positions.
    """
    contig_segments = []
    for motif_segment in contig_string.split("/"):
        if motif_segment[0].isalpha():  # Motif segment
            chain = motif_segment[0]
            if len(motif_segment[1:].split("-")) == 2:
                start, end = map(int, motif_segment[1:].split("-"))
            else:
                start = end = int(motif_segment[1:])
            contig_segments.append({"chain": chain, "start": start, "end": end})
        else:  # Scaffold segment
            scaffold_length = int(motif_segment)
            contig_segments.append({"chain": "scaffold", "length": scaffold_length})
    return contig_segments


def quantize_redesign_positions(redesign_info: str) -> List[str]:
    """
    Parse redesign positions into a list of individual chain-position strings.
    For example, "A19-21;A23" becomes ["A19", "A20", "A21", "A23"].
    """
    redesign_list = []
    if len(redesign_info) == 0: return redesign_list

    for segment in redesign_info.split(";"):
        chain = segment[0]
        if "-" in segment:
            start, end = map(int, segment[1:].split("-"))
            redesign_list.extend([f"{chain}{i}" for i in range(start, end + 1)])
        else:
            redesign_list.append(segment)
    return redesign_list


def superimpose_rmsd(mobile_xyz: np.ndarray, target_xyz: np.ndarray) -> float:
    """Align mobile->target by Kabsch (biotite superimpose), then RMSD via biotite.structure.rmsd."""
    if mobile_xyz.shape != target_xyz.shape or mobile_xyz.size == 0:
        return math.nan
    mobile_aligned, _ = struc.superimpose(target_xyz, mobile_xyz)
    return float(struc.rmsd(target_xyz, mobile_aligned))


def motif_mapping(
    motif_indices: List[int],
    redesign_positions: Optional[str], # Will be `None` if no residues are to be redesigned 
    contig: str
) -> Tuple[Dict, List[str], List[int]]:
    """
    Adjust motif indices to exclude redesign positions based on native redesign positions.

    Args:
        motif_indices (List[int]): Original list of indices in the designed protein.
        redesign_positions (str): Redesign positions in the native protein.
        contig (str): Contig string specifying scaffold and motif segments.

    Returns:
        List[int]: Updated list of motif indices with redesign positions removed.
    """
    # Parse the contig and redesign positions
    contig_segments = parse_contig_to_dict(contig)
    redesign_list = quantize_redesign_positions(redesign_positions) if redesign_positions else []

    # Build a dictionary mapping native positions to motif indices
    native_to_index = {}
    index_pointer = 0

    for segment in contig_segments:
        if segment['chain'] == "scaffold":
            continue  # Skip scaffold segments

        chain = segment["chain"] # A
        start = segment["start"] # 92
        end = segment["end"] # 99

        # Iterate over each native position and map it to the corresponding motif index
        for native_pos in range(start, end + 1):
            native_key = f"{chain}{native_pos}" # A92
            if index_pointer < len(motif_indices):
                native_to_index[native_key] = motif_indices[index_pointer] # {"A92": 12, "A93": 13, "A"}
                index_pointer += 1
            else:
                break

    # Filter out the redesign positions from the mapping
    updated_indices_for_mpnn = [
        index for native_key, index in native_to_index.items()
        if native_key not in redesign_list
    ]

    fixed_native = [k for k in native_to_index.keys() if k not in redesign_list]

    return (native_to_index, redesign_list, updated_indices_for_mpnn, fixed_native)


def check_motif_AA_type(
    design_file: Union[str, Path],
    reference_file: Union[str, Path],
    position_mapping: Dict,
    redesign_list: List,
    output_file: Union[str, Path, biotite.structure.AtomArray]
) -> bool:
    """
    Check if dummy residues placed within motifs and replace them according to positions to be redesigned.

    Args:
      design_file: Designed backbone to be checked.
      reference_file: Motif PDB Files. 
       - If using motif contig, this should be cleaned pure motif pdb file.
       - If using native contig, this should be native pdb file.
      position_mapping: A dictionary mapping motifs positions between reference structure and designed structure
       - e.g. # {"A92": 12, "A93": 13, ......}, where key = positions in native one and value = positions in designed one
       - !Note that we pre-assume that all positions in designed proteins only possessed chain A for now.
       - Complex systems should be handled in a future version.
      redesign_list: A list containing positions to be redesigned in designed structure. 
       Only residues fixed (supplementary set of redesigned positions) would be changed according to reference motif.
      output_file: File to be written. If all residues consistent with reference ones, no output file will be created.
       - If file needs to be output, it will overwrite original file in evaluation directory
       - The original structure with dummy residues will be copied into another sub directory called `original_pdb`
    
    Return:
      A bool value indicating whether are motif AA types are correct. 

    Usage: Set `inference.force_motif_AA_type` to be "True".
    """
    
    design_pdb = strucio.pdb.PDBFile.read(design_file) # AtomArrayStack
    design_array = design_pdb.get_structure()[0] # We assume to take only one model, Get first AtomArray from AtomArrayStack

    reference_pdb = strucio.pdb.PDBFile.read(reference_file)
    reference_array = reference_pdb.get_structure()[0]
    
    # Check if all fixed positions have correct amino acid types
    incompatible_list = []
    for ref_position, design_idx in position_mapping.items():
        if ref_position not in redesign_list:
            assert ref_position[0].isalpha(), f"Reference position {ref_position} does not have chain identity!"
            ref_chain_id = ref_position[0]
            ref_idx = int(ref_position[1:])
            
            ref_aa = reference_array[(reference_array.chain_id==ref_chain_id) & (reference_array.res_id==ref_idx)]
            design_aa = design_array[(design_array.chain_id=="A") & (design_array.res_id==design_idx)] # We consider designed backbones as monomers for now
            
            if design_aa.res_name[0] != ref_aa.res_name[0]:
                incompatible_list.append(design_idx)
    
    # Change Amino acid types if uncorrect ones exist
    if len(incompatible_list) > 0:
        log.warning(f"Residues types in {incompatible_list} in designed backbone not consistent to standard motifs, changed accordingly.")
        for ref_position, design_idx in position_mapping.items():
            if ref_position not in redesign_list:
                ref_chain_id = ref_position[0]
                ref_idx = int(ref_position[1:])
                
                ref_aa = reference_array[(reference_array.chain_id==ref_chain_id) & (reference_array.res_id==ref_idx)]
                design_array.res_name[(design_array.chain_id=="A") & (design_array.res_id==design_idx)] = ref_aa.res_name[0]
            
        modified_file = strucio.pdb.PDBFile()
        modified_file.set_structure(design_array)
        modified_file.write(output_file)
        log.info(f"Overwritten residue types of fixed motif residues into {output_file}, would be used as input for sequence design.")
        return False
    else:
        log.info(f"Residue types in designed backbone are consistent to standard motifs, continue.")
        return True
    

def reindex_pdb_residues(
    original_file: Union[str, Path],
    output_file: Union[str, Path],
    original_start_index: int = 0,
    reindex_start: int = 1
):
    """
    Reindex the starting residue number in a PDB file.
    If the original file already starts from the desired index, no changes are made.
    
    Args:
      original_file: Path to the original PDB file.
      output_file: Path to save the reindexed PDB file.
      original_start_index: The starting residue number in the original PDB file.
      reindex_start: The desired starting residue number in the output PDB file.
    """
    pdb_file = strucio.pdb.PDBFile.read(original_file)
    atom_array = pdb_file.get_structure()[0]
    if atom_array.res_id[0] == reindex_start:
        return True
    else:
        offset = reindex_start - original_start_index
        atom_array.res_id += offset

        modified_pdb = strucio.pdb.PDBFile()
        modified_pdb.set_structure(atom_array)
        modified_pdb.write(output_file)
        log.info(f"Original PDB file starts from residue {original_start_index},\
            reindexed to start from {reindex_start} and saved to {output_file}")
        return False


def get_sidechain_atoms(array: struc.AtomArray) -> struc.AtomArray:
    """Extract sidechain atoms (excluding backbone ones)."""
    aa_mask = struc.filter_amino_acids(array)
    bb_mask = np.isin(array.atom_name, list(BACKBONE_ATOMS))
    return array[aa_mask & ~bb_mask]


def get_residue_subset(array: struc.AtomArray, chain_id: str, res_id: int) -> struc.AtomArray:
    """Extract a specific group of residues by chain and residue IDs."""
    return array[(array.chain_id == chain_id) & (array.res_id == res_id)]


def _residue_atom_pairs(
    native_res: struc.AtomArray,
    design_res: struc.AtomArray,
    atom_mode: Literal["sidechain", "backbone", "all-atom"],
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Extract a pair of atoms from either side-chain, backbone or all-atoms.
    atom_mode
        "sidechain": Extract side chain atoms (excluding backbone atoms)
        "backbone": Extract only backbone atoms
        "all-atom": Extract both side chain and backbone atoms 
    """
    if atom_mode == "sidechain":
        native_sel = get_sidechain_atoms(native_res)
        design_sel = get_sidechain_atoms(design_res)
    elif atom_mode == "backbone":
        n_mask = np.isin(native_res.atom_name, list(BACKBONE_ATOMS))
        d_mask = np.isin(design_res.atom_name, list(BACKBONE_ATOMS))
        native_sel = native_res[n_mask]
        design_sel = design_res[d_mask]
    elif atom_mode == "all-atom":
        native_sel = native_res
        design_sel = design_res

    n_names = np.array(native_sel.atom_name)
    d_names = np.array(design_sel.atom_name)
    common_names = sorted(set(n_names).intersection(set(d_names)))
    if len(common_names) == 0:
        return [], []

    n_xyz = []
    d_xyz = []
    for aname in common_names:
        n_atom = native_sel[native_sel.atom_name == aname]
        d_atom = design_sel[design_sel.atom_name == aname]
        if n_atom.array_length() == 0 or d_atom.array_length() == 0:
            continue
        n_xyz.append(np.asarray(n_atom.coord[0], dtype=float))
        d_xyz.append(np.asarray(d_atom.coord[0], dtype=float))

    return n_xyz, d_xyz


def _compute_metrics_for_positions(
    design_array: struc.AtomArray,
    native_motif_array: struc.AtomArray,
    mapping: Tuple[Dict[str, str], List, List, List],
    atom_mode: Literal["sidechain", "backbone", "all-atom"],
    require_same_aa: bool,
    skip_native_unk: bool,
    design_chain: str = "A"
) -> Tuple[float, int, int]:
    native_coords = []
    design_coords = []
    used_res = 0

    for native_key in mapping[3]:
        # Get indices in reference motif
        scaffold_idx = mapping[0].get(native_key)
        if scaffold_idx is None:
            continue
        native_chain = native_key[0]
        native_resid = int(native_key[1:])

        native_res = get_residue_subset(native_motif_array, native_chain, native_resid)
        if native_res.array_length() == 0: continue
        if skip_native_unk and native_res.res_name[0] == "UNK": continue

        design_res = get_residue_subset(design_array, design_chain, scaffold_idx)
        if design_res.array_length() == 0: continue
        if require_same_aa and design_res.res_name[0] != native_res.res_name[0]: continue

        n_xyz, d_xyz = _residue_atom_pairs(native_res, design_res, atom_mode=atom_mode)
        if len(n_xyz) == 0: 
            continue
        native_coords.extend(n_xyz)
        design_coords.extend(d_xyz)
        used_res += 1

    if len(native_coords) < 3:
        return math.nan, len(native_coords), used_res

    n_arr = np.vstack(native_coords)
    d_arr = np.vstack(design_coords)
    rmsd_val = superimpose_rmsd(d_arr, n_arr)

    return rmsd_val, int(len(native_coords)), used_res


def compute_sidechain_rmsd(
    refolded_path: Union[str, Path],
    native_motif_array: struc.AtomArray,
    mapping: Tuple,
    design_chain: str = "A"
) -> Tuple[float, float, int, int, int, int]:
    design_array = strucio.load_structure(refolded_path, model=1)

    sidechain_rmsd, sidechain_n_atoms, sidechain_nres = _compute_metrics_for_positions(
        design_array=design_array,
        native_motif_array=native_motif_array,
        mapping=mapping,
        atom_mode="sidechain",
        require_same_aa=True,
        skip_native_unk=True,
        design_chain=design_chain
    )

    aa_rmsd, aa_n_atoms, aa_nres = _compute_metrics_for_positions(
        design_array=design_array,
        native_motif_array=native_motif_array,
        mapping=mapping,
        atom_mode="all-atom",
        require_same_aa=True,
        skip_native_unk=True,
        design_chain=design_chain
    )

    return [sidechain_rmsd, aa_rmsd, sidechain_n_atoms, sidechain_nres, aa_n_atoms, aa_nres]


# ------------------------Utils for Steric Clashes--------------------
# Adapted from https://github.com/lujiarui/Str2Str/blob/main/src/metrics/metrics.py

def distance_matrix_ca(coords: np.ndarray) -> np.ndarray:
    """Calculate pairwise CA distance matrix for batched or single-chain coords."""
    assert coords.ndim in (2, 3), f"CA coords should be 2D or 3D, got {coords.shape}"
    dX = coords[..., None, :, :] - coords[..., None, :]
    return np.sqrt(np.sum(dX**2, axis=-1))


def pairwise_distance_ca(coords: np.ndarray, k: int = 1) -> np.ndarray:
    """Return upper-triangle pairwise distances, excluding neighbors by k."""
    assert coords.ndim in (2, 3), f"CA coords should be 2D or 3D, got {coords.shape}"
    dist = distance_matrix_ca(coords)
    L = dist.shape[-1]
    row, col = np.triu_indices(L, k=k)
    return dist[..., row, col]


def _steric_clash(
    coords: np.ndarray,
    ca_vdw_radius: float = 1.7,
    allowable_overlap: float = 0.4,
    k_exclusion: int = 0,
) -> np.ndarray:
    """
    Calculate number of CA steric clashes for each structure in batch.
    Returns shape (B,).
    """
    assert np.isnan(coords).sum() == 0, "coords should not contain nan"
    assert coords.ndim in (2, 3), f"CA coords should be 2D or 3D, got {coords.shape}"
    assert k_exclusion >= 0, "k_exclusion should be non-negative"

    if coords.ndim == 2:
        coords = coords[None, ...]

    bar = 2 * ca_vdw_radius - allowable_overlap
    pwd = pairwise_distance_ca(coords, k=k_exclusion + 1)
    assert pwd.ndim == 2, f"pwd should be 2D, got {pwd.shape}"
    n_clash = np.sum(pwd < bar, axis=-1)
    return n_clash.astype(int)


def load_ca_coords(pdb_path: Path) -> np.ndarray:
    """Load CA coordinates from a PDB structure."""
    atom_array = strucio.load_structure(pdb_path, model=1)
    atom_array = atom_array[struc.filter_amino_acids(atom_array)]
    ca_mask = atom_array.atom_name == "CA"
    ca_atoms = atom_array[ca_mask]

    if ca_atoms.array_length() == 0:
        raise ValueError(f"No CA atoms found in {pdb_path}")

    return np.asarray(ca_atoms.coord, dtype=np.float32)


def clash_metrics_from_pdb(
    pdb_path: Path,
    ca_vdw_radius: float = 1.7,
    allowable_overlap: float = 0.4,
    k_exclusion: int = 0,
) -> tuple[int, float, int]:
    """
    Return (num_ca_clashes, clash_score, n_atoms).
    clash_score is number of clashes per 1000 CA atoms.
    """
    ca_coords = load_ca_coords(pdb_path)
    n_atoms = int(ca_coords.shape[0])
    n_clash = int(
        _steric_clash(
            ca_coords,
            ca_vdw_radius=ca_vdw_radius,
            allowable_overlap=allowable_overlap,
            k_exclusion=k_exclusion,
        )[0]
    )
    clash_score = (1000.0 * n_clash / n_atoms) if n_atoms > 0 else 0.0
    return n_clash, clash_score, n_atoms


# ------------------------Utils for Unconditional Generation--------------------

def analyze_success_rate_uncond(
        merged_data: Union[str, Path, pd.DataFrame],
        group_mode: str = "all",
        prefix: str = "esm",
        metric: str = 'tm_score',
        threshold: Optional[Union[str, float, int]]=None,
    ):

    # Define success criteria for each sample
    merged_data = pd.read_csv(merged_data) if isinstance(merged_data, str) or isinstance(merged_data, Path) else merged_data

    #merged_data['seq_hit'] = (merged_data['rmsd'] < 2) & (merged_data['motif_rmsd'] < 1)
    if metric == 'rmsd':
        if threshold is not None:
            merged_data['seq_hit'] = (merged_data['rmsd'] < threshold)
        else:
            merged_data['seq_hit'] = (merged_data['rmsd'] < 2.0)
    elif metric == 'tm_score':
        if threshold is not None:
            merged_data['seq_hit'] = (merged_data['tm_score'] > threshold)
        else:
            merged_data['seq_hit'] = (merged_data['tm_score'] > 0.5)

    # Group by 'backbone_path' and aggregate the success criteria
    group_success = merged_data.groupby('backbone_path').agg({
        'seq_hit': 'any',
    }).rename(columns={
        'seq_hit': 'Success',
    })

    # Join the aggregated results back to the original DataFrame
    merged_data = merged_data.merge(group_success, on='backbone_path', how='left')

    successful_backbones = set()
    if group_mode == 'all':
        success_count = merged_data[merged_data['Success'] == True]['backbone_path'].nunique()
        successful_backbones = set(merged_data[merged_data['Success'] == True]['backbone_path'])
    elif group_mode == 'PDB id':
        success_count = dict.fromkeys(merged_data['PDB id'].unique(), 0)
        success_per_pdb = merged_data[merged_data['Success'] == True].groupby('PDB id')['backbone_path'].nunique()
        success_count.update(success_per_pdb.to_dict())

        successful_backbones = set(merged_data[merged_data['Success'] == True]['backbone_path'])

    #print(f'merged_data.columns: {set(merged_data.columns)}')

    summary_data = merged_data.drop(columns=["header", "mpnn_score"], inplace=False)
    #print(f'summary_data.columns: {set(summary_data.columns)}\nmerged_data.columns: {set(merged_data.columns)}\n')

    # Find best contender
    designable_scaffolds = merged_data[merged_data["rmsd"] < 2] if metric == 'rmsd' else merged_data[merged_data["tm_score"] > 0.5]
    if not designable_scaffolds.empty:
        best_contender = designable_scaffolds.loc[designable_scaffolds["rmsd"].idxmin()] if metric == 'rmsd' else designable_scaffolds.loc[designable_scaffolds["tm_score"].idxmax()]
        best_contender_df = best_contender.to_frame().T
    else:
        best_contender = None


    return merged_data, summary_data, success_count, successful_backbones, best_contender_df


def write_auxiliary_metrics_uncond(
    stored_path: Union[str, Path],
    auxiliary_results: Union[str, Path, pd.DataFrame],
    prefix: Optional[str] = None
) -> None:

    if not auxiliary_results is None:
        best_contender_rmsd = auxiliary_results['rmsd'].iloc[0]
        best_contender_tm_score = auxiliary_results['tm_score'].iloc[0]
        best_contender_scaffold = auxiliary_results['backbone_path'].iloc[0]
        best_contender_refold = auxiliary_results['sample_path'].iloc[0]
    else:
        best_contender_rmsd = "\\"
        best_contender_tm_score = "\\"
        best_contender_scaffold = "\\"
        best_contender_refold = "\\"

    # Formatting
    summary_table = [
        ["Evaluated Protein Set", os.path.basename(os.path.normpath(stored_path))],
        ["Best Contender (Scaffold)", best_contender_scaffold],
        ["Best Contender (Refolded Structure)", best_contender_refold],
        ["Scaffold TM-score of Best Contender", best_contender_tm_score],
        ["Scaffold RMSD of Best Contender (Å)", best_contender_rmsd],
    ]
    formatted_table = tabulate(summary_table, tablefmt="grid", numalign="center")

    with open (os.path.join(stored_path, f'{prefix}_auxiliary_metrics.txt'), 'w') as f:
        f.write('----------Auxiliary Metrics----------\n\n')
        f.write(f'The following are auxiliary metrics for {os.path.abspath(stored_path)}:\n\n')
        f.write(formatted_table + "\n")

