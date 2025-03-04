"""
- Usage:
```bash
# Creating PhantomWiki documents and questions:
python -m phantom_wiki -od <output path>
```
"""

from .facts import question_parser
from .facts.family import fam_gen_parser
from .facts.friends import friend_gen_parser
from .generate_dataset import generate_dataset
from .utils import get_parser


def main():
    # We combine a base parser with all the generators' parsers
    parser = get_parser(
        parents=[
            fam_gen_parser,
            friend_gen_parser,
            question_parser,
        ]
    )
    args = parser.parse_args()

    generate_dataset(**vars(args))


if __name__ == "__main__":
    main()
