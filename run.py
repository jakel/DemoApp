from DemoApp import main
from DemoApp.utils import Map
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", help="set flask to debug mode",
                    action="store_true")
args = parser.parse_args()

def run():
    main(Map(debug=args.debug))

if __name__ == '__main__':
    run()
