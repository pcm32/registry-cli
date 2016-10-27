import unittest

__author__ = 'pmoreno'

import sys
sys.path.append('../../')

from Image import DockerImage, AccumulatedUsage, DistanceMatrix


class TestImage(unittest.TestCase):
    def test_get_size(self):
        image = DockerImage('my_image','latest')
        image.add_layer('352617', size=5)
        image.add_layer('35asdhak', size=10)
        self.assertTrue(image.get_size() == 15, "Should have size 15")

    def test_shared_data(self):
        image = DockerImage('my_image', 'latest')
        image.add_layer('352617', size=5)
        image.add_layer('3526171', size=5)
        image.add_layer('35asdhak', size=10)

        second_image = DockerImage('second_image', 'latest')
        second_image.add_layer('352617', size=5)
        second_image.add_layer('3526171', size=5)
        second_image.add_layer('3526asda17', size=20)

        self.assertEqual(image.shared_data(second_image), 10, "Should have shared size equal to 10 but it is "+str(image.shared_data(second_image)))

class TestAccumlatedUsage(unittest.TestCase):
    def test_current_usage(self):
        image = DockerImage('my_image', 'latest')
        image.add_layer('352617', size=500.0*(1024**2)) # 500 MB
        image.add_layer('35asdhak', size=2.0*(1024**3)) # 2 GB

        second_image = DockerImage('second_image', 'latest')
        second_image.add_layer('352617', size=500.0*(1024**2)) # 500 MB
        second_image.add_layer('3526asda17', size=3.0*(1024**3)) # 3 GB

        accumulator = AccumulatedUsage()
        accumulator.add(image)
        accumulator.add(second_image)

        expected = 500.0*(1024**2) + 2.0*(1024**3) + 3.0*(1024**3)
        self.assertEqual(accumulator.get_current_usage(), expected, "Accumulated space should be "+str(expected)+", but is "+str(accumulator.get_current_usage()))

class TestDistanceMatrix(unittest.TestCase):
    def test_get_closest(self):
        image = DockerImage('first_image', 'latest')
        image.add_layer('352617', size=500.0 * (1024 ** 2))  # 500 MB
        image.add_layer('35asdhak', size=2.0 * (1024 ** 3))  # 2 GB

        second_image = DockerImage('second_image', 'latest')
        second_image.add_layer('352617', size=500.0 * (1024 ** 2))  # 500 MB
        second_image.add_layer('3526asda17', size=3.0 * (1024 ** 3))  # 3 GB

        third_image = DockerImage('third_image', 'latest')
        third_image.add_layer('352617', size=500.0 * (1024 ** 2))  # 500 MB
        third_image.add_layer('3526asda17', size=3.0 * (1024 ** 3))  # 3 GB
        third_image.add_layer('3526as17', size=0.1 * (1024 ** 3))  # ~100 MB

        dist_mat = DistanceMatrix()
        dist_mat.add_image(image)
        dist_mat.add_image(second_image)
        dist_mat.add_image(third_image)

        # third should be closest to second
        closest_to_third = dist_mat.get_closest_to(third_image)
        self.assertEqual(closest_to_third.full_name(), second_image.full_name(), "Second image should be closest to third, yet we are getting "+closest_to_third.full_name())


if __name__ == '__main__':
    unittest.main()