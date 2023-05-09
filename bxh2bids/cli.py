r"""Convert MRI data from BIAC into BIDS format

Notes:
    If no proj-dir passed, uses $BIDS_DIR

Examples:

    bxh2bids --biac-dirs 01011900_12345

    bxh2bids --proj-dir /path/bids_dir --biac-dirs 01011900_12345 01021900_56789

"""

# %%
import os
import sys
import textwrap
from argparse import ArgumentParser, RawTextHelpFormatter

# %%
def _get_args():
    """Get and parse arguments."""
    parser = ArgumentParser(
        description=__doc__, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "-p",
        "--proj-dir",
        type=str,
        default='None',
        help=textwrap.dedent(
            """\
            Path to BIDS-formatted project directory
            """
        ),
    )

    required_args = parser.add_argument_group("Required Arguments")
    required_args.add_argument(
        "-b",
        "--biac-dirs",
        nargs="+",
        help=textwrap.dedent(
            """\
            BIAC directory IDs to convert, in the form of MMDDYYYY_#####.
            (e.g. 01011900_12345)
            """
        ),
        type=str,
        required=True,
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    return parser


# %%
def main():
    """Setup working environment."""

    # Capture CLI arguments
    args = _get_args().parse_args()
    biac_dirs = args.biac_dirs
    proj_dir = args.proj_dir

    # Check proj_dir. If not passed, check for env variable.
    if proj_dir == 'None':
        try:
            for element in os.environ:
                value = os.environ[element]
                print(f"{element}: {value}")
            proj_dir = os.environ["BIDS_DIR"]
        except KeyError:
            print(f"Global variable BIDS_DIR is not set and no proj_dir passed!")
            sys.exit(1)

    if not os.path.exists(proj_dir):
        raise FileNotFoundError(f"Expected to find project directory : {proj_dir}")

    import bxh2bids.run_bxh2bids as rb2b
    rb2b.bidsify(proj_dir, biac_dirs)



if __name__ == "__main__":

    # Require proj env
    env_found = [x for x in sys.path if "nature" in x]
    if not env_found:
        print("\nERROR: missing required project environment 'nature'.")
        print("\tHint: $labar_env nature\n")
        sys.exit(1)
    main()

# %%