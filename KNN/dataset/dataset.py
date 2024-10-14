import random, pickle
import argparse


def generate_random_dataset(num_points: int, max_bound: float = 1e4) -> list[tuple[float]]:
    """Generates N random points uniformly sampled from the 2D space
    within a given bound"""

    points = []
    for i in range(num_points):
        x = random.uniform(-max_bound, max_bound + 1)
        y = random.uniform(-max_bound, max_bound + 1)
        points.append((x, y))
    
    return points

def create_dataset(num_points: int, filepath: str):
    """Creates the dataset and stores it in a pkl file"""

    points = generate_random_dataset(num_points)
    with open(filepath, 'wb') as outfile:
        pickle.dump(points, outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate random dataset")
    parser.add_argument("num_points", type=int, help="Number of points to generate.")
    parser.add_argument("filepath", type=str, help="Path of file where to save the dataset.")
    
    args = parser.parse_args()
    create_dataset(args.num_points, args.filepath)

