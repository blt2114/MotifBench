# Check that a motif, and config file are specified
if [ "$#" -lt 1 ]; then
    echo "Usage: ./launch_all.sh <config.txt> [refolding_options...]"
    echo "Example: ./launch_all.sh config.txt --ca-only"
    exit 1
fi
# Source the configuration file
config_path=$1
shift
refolding_options=("$@")
source "$config_path"

# Ensure necessary variables are set in the config file
if [ -z "$scaffold_base_dir" ] || [ -z "$foldseek_db_path" ] || [ -z \
    "$base_output_dir" ] || [ -z "$benchmark_dir" ] || [ -z "$python_path" ] ; then
    echo "Error: Configuration file is missing necessary settings."
    echo "Ensure it includes 'scaffold_base_dir', 'foldseek_db_path', \
        'base_output_dir', 'python_path' and 'benchmark_dir'."
    exit 1
fi

# Check validity of scaffold lengths
$python_path $benchmark_dir/scripts/length_check.py -i $scaffold_base_dir -o $scaffold_base_dir

log_dir=$base_output_dir/logs/
mkdir -p $log_dir
ls $scaffold_base_dir | grep -E '^[0-9]{2}_.{4}$' | while read motif_name; do
    out_fn=$log_dir/$motif_name.%j.out
    err_fn=$log_dir/$motif_name.%j.err
    sbatch --output=$out_fn --error=$err_fn $benchmark_dir/scripts/evaluate_bbs.sh $motif_name $config_path "${refolding_options[@]}"
done
