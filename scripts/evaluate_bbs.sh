#!/usr/bin/bash
#SBATCH --time=12:00:00
#SBATCH -p owners
#SBATCH --gpus=1
#SBATCH -c 4
#SBATCH --mem=128GB

# Check that a motif, and config file are specified
if [ "$#" -lt 2 ]; then
    echo "Usage: ./evaluate_bbs.sh motif_name config_file [refolding_options]"
    echo "For example: ./evaluate_bbs.sh 01_1LDB config.txt --ca-only"
    exit 1
fi

motif_name=$1
config_file=$2

shift 2

hydra_overrides=()
for option in "$@"; do
    case "$option" in
        --ca-only)
            hydra_overrides+=("inference.CA_only=True")
            ;;
        *=*)
            hydra_overrides+=("$option")
            ;;
        *)
            echo "Error: Unknown option '$option'"
            exit 1
            ;;
    esac
done

echo "Running on motif: $motif_name"

# Check if the configuration file exists
if [ ! -f "$config_file" ]; then
    echo "Error: Configuration file '$config_file' does not exist."
    exit 1
fi

# Source the configuration file
source "$config_file"

# Ensure necessary variables are set in the config file
if [ -z "$scaffold_base_dir" ] || [ -z "$foldseek_db_path" ] || [ -z \
    "$base_output_dir" ] || [ -z "$benchmark_dir" ] || [ -z "$python_path" ] ; then
    echo "Error: Configuration file is missing necessary settings."
    echo "Ensure it includes 'scaffold_base_dir', 'foldseek_db_path', \
        'base_output_dir', and 'benchmark_dir'."
    exit 1
fi

# Set derived paths
output_dir=$base_output_dir/$motif_name/
bb_dir=$scaffold_base_dir/$motif_name

# Create output directory if it doesn't exist
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi

# Make motif_info.csv from scaffold_info.csv
motif_pdb_path=$benchmark_dir/motif_pdbs/$motif_name".pdb"
$python_path $benchmark_dir/scripts/write_motifInfo_from_scaffoldInfo.py \
    $bb_dir/scaffold_info.csv $motif_pdb_path $bb_dir/motif_info.csv

# Check the validity of number of motif segments
$python_path $benchmark_dir/scripts/check_segment_validity.py \
    --input $benchmark_dir/test_cases.csv --test $bb_dir/motif_info.csv

# Run Scaffold-Lab for evaluation
$python_path $benchmark_dir/Scaffold-Lab/motif_refolding.py \
    inference.motif_csv_path=$bb_dir/motif_info.csv \
    inference.backbone_pdb_dir=$bb_dir \
    inference.motif_pdb=$motif_pdb_path \
    inference.output_dir=$output_dir \
    evaluation.foldseek_database=$foldseek_db_path \
    inference.force_motif_AA_type=True \
    "${hydra_overrides[@]}"