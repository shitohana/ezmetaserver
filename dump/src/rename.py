import json

import pandas as pd


# Define the mapping for common metadata fields
COLUMN_RENAME_MAP = {
    "EXPERIMENT.@accession": "Experiment Accession",
    "EXPERIMENT.@alias": "Experiment Alias",
    "EXPERIMENT.TITLE": "Experiment Title",
    "EXPERIMENT.IDENTIFIERS.PRIMARY_ID": "Experiment ID",
    "STUDY.@accession": "Study Accession",
    "STUDY.DESCRIPTOR.STUDY_TITLE": "Study Title",
    "STUDY.DESCRIPTOR.STUDY_ABSTRACT": "Study Abstract",
    "STUDY.IDENTIFIERS.EXTERNAL_ID.#text": "BioProject ID",
    "SAMPLE.@accession": "Sample Accession",
    "SAMPLE.@alias": "Sample Alias",
    "SAMPLE.SAMPLE_NAME.SCIENTIFIC_NAME": "Scientific Name",
    "SAMPLE.SAMPLE_NAME.TAXON_ID": "Taxon ID",
    "SAMPLE.DESCRIPTION": "Sample Description",
    "EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_NAME": "Library Name",
    "EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_STRATEGY": "Library Strategy",
    "EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_SOURCE": "Library Source",
    "EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_SELECTION": "Library Selection",
    "EXPERIMENT.DESIGN.LIBRARY_DESCRIPTOR.LIBRARY_LAYOUT": "Library Layout",
    "PLATFORM.OXFORD_NANOPORE.INSTRUMENT_MODEL": "Instrument Model",
    "PLATFORM.ILLUMINA.INSTRUMENT_MODEL": "Instrument Model",
    "PLATFORM.PACBIO_SMRT.INSTRUMENT_MODEL": "Instrument Model",
    "RUN_SET.RUN.@accession": "Run Accession",
    "RUN_SET.RUN.@alias": "Run Alias",
    "RUN_SET.RUN.@total_spots": "Total Spots",
    "RUN_SET.RUN.@total_bases": "Total Bases",
    "RUN_SET.RUN.@size": "File Size (bytes)",
}


# Extract download links from 'RUN_SET.RUN.SRAFiles.SRAFile'
def extract_links(entry):
    try:
        files = json.loads(entry) if isinstance(entry, str) else entry
        if isinstance(files, list):
            return [f.get("@url") for f in files if "@url" in f]
        elif isinstance(files, dict):
            return [files.get("@url")] if "@url" in files else []
        return []
    except Exception:
        return []


def select_and_rename_common_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selects and renames common metadata columns in a sequencing experiments DataFrame,
    and extracts all available download links into a 'Download Links' column.

    Parameters:
        df (pd.DataFrame): Original DataFrame with flattened JSON column keys.

    Returns:
        pd.DataFrame: Cleaned and renamed DataFrame with download links.
    """
    # Filter existing columns for renaming
    existing = {k: v for k, v in COLUMN_RENAME_MAP.items() if k in df.columns}
    cleaned_df = df[list(existing.keys())].rename(columns=existing)

    if "RUN_SET.RUN.SRAFiles.SRAFile" in df.columns:
        cleaned_df["Download Links"] = df["RUN_SET.RUN.SRAFiles.SRAFile"].apply(extract_links)
    else:
        cleaned_df["Download Links"] = [[] for _ in range(len(df))]

    return cleaned_df