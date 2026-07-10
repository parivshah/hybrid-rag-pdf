"""Generate data/sample-policy.pdf  -  synthetic home insurance policy for demos."""

from pathlib import Path

from fpdf import FPDF

POLICY_TEXT = """
PolicyPulse Homeowners Insurance Policy
Policy Number: DEMO-HO-2026-001
Effective Date: January 1, 2026

SECTION 1  -  COVERED PROPERTY
This policy insures your dwelling, attached structures, and personal property against
direct physical loss from covered perils, subject to the limits and exclusions below.

SECTION 2  -  COVERED PERILS
We cover sudden and accidental direct physical loss from:
- Fire or lightning
- Windstorm or hail
- Explosion
- Riot or civil commotion
- Vandalism
- Theft
- Falling objects
- Weight of ice, snow, or sleet
- Accidental discharge or overflow of water or steam from within a plumbing, heating,
  air conditioning, or automatic fire protective sprinkler system, or from a household appliance

SECTION 3  -  DEDUCTIBLES
3.1 All Other Perils Deductible: $500 per occurrence.
3.2 Wind and Hail Deductible: $1,000 per occurrence, or 1% of Coverage A dwelling limit,
    whichever is greater. This deductible applies separately to each wind or hail loss.
3.3 Named Storm Deductible: $2,500 per occurrence when a named storm is declared by the
    National Weather Service.

SECTION 4  -  EXCLUSIONS
We do not insure for loss caused directly or indirectly by any of the following.
Such loss is excluded regardless of any other cause or event contributing concurrently
or in any sequence to the loss.

4.1 Flood: Surface water, waves, tidal water, overflow of a body of water, or spray from
    any of these, whether or not driven by wind.

4.2 Gradual Water Damage: Continuous or repeated seepage or leakage of water over a period
    of 14 days or more, including related mold, fungus, or wet rot.

4.3 Mold, Fungus, or Wet Rot: Mold, fungus, or wet rot unless hidden within walls, ceilings,
    or floors and caused by a covered peril that occurs suddenly and accidentally. We will
    pay up to $5,000 for mold remediation under this exception.

4.4 Earth Movement: Earthquake, landslide, mudslide, sinkhole, or earth sinking, rising,
    or shifting.

4.5 Intentional Acts: Loss arising out of any act committed by an insured with intent to
    cause a loss.

4.6 Wear and Tear: Deterioration, rust, corrosion, mechanical breakdown, or latent defect.

SECTION 5  -  WATER DAMAGE COVERAGE
5.1 Sudden Discharge: We cover sudden and accidental discharge of water from plumbing,
    appliances, or HVAC systems. Example: a burst pipe that floods a basement is covered,
    minus your deductible.
5.2 Sump Pump Failure: We cover damage from water that enters through a sump well, sump pump,
    or related equipment if the failure is sudden and accidental. Backup coverage limit: $10,000.
5.3 Sewer Backup: Optional coverage. Not included unless endorsed. Endorsement HO-503 adds
    $5,000 sewer and drain backup coverage.

SECTION 6  -  PERSONAL PROPERTY
Coverage C limit: $150,000. Special limits apply to jewelry ($1,500), firearms ($2,500),
and business property on premises ($2,500).

SECTION 7  -  LOSS OF USE
If a covered loss makes your residence uninhabitable, we pay additional living expenses
up to 20% of Coverage A for the shortest time required to repair or replace the dwelling.

SECTION 8  -  LIABILITY COVERAGE
Personal liability: $300,000 per occurrence. Medical payments to others: $5,000 per person.

SECTION 9  -  CLAIMS REPORTING
Report all losses within 60 days. Mitigate further damage. Keep damaged property for inspection.
Failure to report promptly may reduce or deny coverage.

SECTION 10  -  POLICY DEFINITIONS
Named Insured: The person or persons named on the declarations page.
Occurrence: An accident, including continuous or repeated exposure to substantially the same
general harmful conditions.
Sudden and Accidental: Unexpected and not intended, occurring at an identifiable time and place.

This is a synthetic demonstration policy for PolicyPulse. It is not a real insurance contract.
"""


def main() -> None:
    output = Path(__file__).resolve().parent.parent / "data" / "sample-policy.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for paragraph in POLICY_TEXT.strip().split("\n\n"):
        pdf.multi_cell(0, 6, paragraph.strip())
        pdf.ln(2)

    pdf.output(str(output))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
