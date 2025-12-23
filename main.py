import argparse
import logging
import sys
from utils.config_manager import ConfigManager
from pipeline import GameAnalysisPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    config = ConfigManager().config
    parser = argparse.ArgumentParser(description='Basketball Video Analysis')
    parser.add_argument('input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_video', type=str, default=config.get('output_video_path', 'output_videos/output_video.avi'),
                        help='Path to output video file')
    parser.add_argument('--stub_path', type=str, default=config.get('stubs_default_path', 'stubs'),
                        help='Path to stub directory')
    return parser.parse_args()

def main():
    args = parse_args()
    
    pipeline = GameAnalysisPipeline()
    pipeline.run(
        input_video_path=args.input_video,
        output_video_path=args.output_video,
        stub_path=args.stub_path
    )

if __name__ == '__main__':
    main()
