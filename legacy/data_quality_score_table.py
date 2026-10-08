import numpy as np
import pandas as pd


def generate_data_quality_scores(input_csv, output_csv):
    print("Loading master table...")
    # Load only the columns we strictly need to maximize memory efficiency
    cols_to_use = ["PUBCHEM_CID", "UniProtKB_ID", "pPotency"]
    df = pd.read_csv(input_csv, usecols=cols_to_use)

    # Drop any rows missing crucial compound, target, or potency data
    df = df.dropna(subset=cols_to_use)

    # Convert pPotency (-log10 Molar) back to linear Molar concentration for accurate CV%
    #print("Computing linear concentration for CV% calculations...")
    #df["Molar_Conc"] = 10 ** (-df["pPotency"])

    print("Grouping by compound-target pairs and computing statistics...")
    # Group by unique compound-target combinations
    grouped = df.groupby(["PUBCHEM_CID", "UniProtKB_ID"])

    # Aggregate metrics
    # Note: 'std' automatically uses ddof=1 (sample standard deviation)
    quality_df = grouped.agg(
        n_observations=("pPotency", "size"),
        mean_pPotency=("pPotency", "mean"),
        SD=("pPotency", "std"),
    #    Molar_Mean=("Molar_Conc", "mean"),
    #    Molar_Std=("Molar_Conc", "std"),
    ).reset_index()

    print("Calculating true linear Coefficient of Variation (CV%)...")
    # CV% = (Standard Deviation / Mean) * 100 on the linear concentration scale
    quality_df["CV%"] = (quality_df["SD"] / quality_df["mean_pPotency"]) * 100

    # Fill NaNs for pairs with only 1 observation (where Standard Deviation cannot be calculated)
    quality_df["SD"] = quality_df["SD"].fillna(0.0)
    quality_df["CV%"] = quality_df["CV%"].fillna(0.0)

    # Drop the temporary linear columns used for the CV% calculation
    #quality_df = quality_df.drop(columns=["Molar_Mean", "Molar_Std"])

    # Rename columns to match your exact requested format
    #quality_df = quality_df.rename(
    #    columns={"mean_pPotency": "mean pPotency", "CV%": "CV%"}
    #)

    # Save to disk
    print(f"Saving quality scores to {output_csv}...")
    quality_df.to_csv(output_csv, index=False)
    print("Done! Data quality file successfully generated.")


if __name__ == "__main__":
    # Adjust paths if your files are located in different directories
    input_file = "data/final/CINTA-Chem_Master_Observations.csv"
    output_file = "data/final/CINTA-Chem_Data_Quality.csv"

    generate_data_quality_scores(input_file, output_file)
