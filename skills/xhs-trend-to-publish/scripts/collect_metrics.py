import argparse
from datetime import datetime
from bootstrap import ROOT
from common import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()

    out = {
        'run_id': args.run_id,
        'stage': 'metrics',
        'collected_at': datetime.now().isoformat(),
        'metrics': {
            'view': 0,
            'like': 0,
            'comment': 0,
            'collect': 0,
            'share': 0,
        },
        'comment_summary': {
            'top_questions': [],
            'sentiment': 'unknown'
        }
    }
    out_path = ROOT / 'data' / 'metrics' / f'{args.run_id}.json'
    write_json(out_path, out)
    print(out_path)


if __name__ == '__main__':
    main()
