#!/usr/bin/env python
"""Create a list of markers that do not match the VCF."""
import re
import shutil
from pathlib import Path
from typing import List

import typer

from cgr_gwas_qc.parsers import bim
from cgr_gwas_qc.parsers.vcf import VariantFile

app = typer.Typer(add_completion=False)


@app.command()
def main(
    bed_in: Path = typer.Argument(
        ..., help="A multi-sample plink bed file.", exists=True, readable=True
    ),
    bim_in: Path = typer.Argument(
        ..., help="A multi-sample plink BIM file.", exists=True, readable=True
    ),
    fam_in: Path = typer.Argument(
        ..., help="A multi-sample plink FAM file.", exists=True, readable=True
    ),
    vcf_in: Path = typer.Argument(..., help="The 1KG VCF file.", exists=True, readable=True),
    bed_out: Path = typer.Argument(
        ...,
        help="Just a copy of `bed_in`, done to keep naming schema simple.",
        file_okay=True,
        writable=True,
    ),
    bim_out: Path = typer.Argument(
        ...,
        help="A BIM file where alleles are corrected to be on the same strand as the VCF.",
        file_okay=True,
        writable=True,
    ),
    fam_out: Path = typer.Argument(
        None,
        help="Just a copy of `fam_in`, done to keep naming schema simple.",
        file_okay=True,
        writable=True,
    ),
):
    """Compares a plink BIM file with a VCF and updates IDs to match VCF.

    This script will also use the nucleotide complements of alleles to match
    the VCF.

    .. note::
        The BED_OUT and FAM_OUT are just copies of the input files. PLINK and
        GRAF operate on the entire set of plink binary files so this will
        make using this output easier.

    """
    with VariantFile(vcf_in, "r") as vcf, bim.open(bim_in) as bin, bim.open(bim_out, "w") as bout:
        for record in bin:
            if not record.get_record_problems():
                update_record_id(record, vcf)
            bout.write(record)

    shutil.copyfile(bed_in, bed_out)
    shutil.copyfile(fam_in, fam_out)


def update_record_id(b_record: bim.BimRecord, vcf: VariantFile):
    """Update the variant ID using the VCF IDs if present."""
    b_record.id = extract_rsID(b_record.id)  # convert IDs like GSA-rs#### to rs####

    for v_record in vcf.fetch(b_record.chrom, b_record.pos - 1, b_record.pos):
        if b_record.pos != v_record.pos:
            # positions aren't the same, this should never happen b/c we are using fetch
            continue

        if any("<" in alt for alt in v_record.alts):
            continue

        if v_record.id is None or not v_record.id.startswith("rs"):
            # No rsID to update with
            continue

        if alleles_equal(b_record.alleles, v_record.alleles) or alleles_equal(
            b_record.complement_alleles(), v_record.alleles
        ):
            b_record.id = v_record.id
            return


def extract_rsID(variant_id: str) -> str:
    match = re.search(r"rs\d+", variant_id)
    return match.group() if match else variant_id


def alleles_equal(bim: List[str], vcf: List[str]) -> bool:
    return sorted(bim) == sorted(vcf)


if __name__ == "__main__":
    if "snakemake" in locals():
        defaults = {}
        defaults.update({k + "_in": Path(v) for k, v in snakemake.input.items()})  # type: ignore # noqa
        defaults.update({k + "_out": Path(v) for k, v in snakemake.output.items()})  # type: ignore # noqa
        main(**defaults)
    else:
        app()
