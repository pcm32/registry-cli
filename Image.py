

class DockerImage(object):

    def __init__(self, name, tag):
        self.__name = name
        self.__tag = tag
        self.__layers = {}

    def add_layer(self, digest, size):
        self.__layers[digest] = size

    def get_layers(self):
        return self.__layers

    def get_size(self):
        total_size = 0
        for key, size in self.get_layers().items():
            total_size += size
        return total_size

    def full_name(self):
        return self.__name+":"+self.__tag

    def shared_data(self, other_docker_image):

        external_layers = other_docker_image.get_layers()
        total_shared = 0
        for key, size in self.get_layers().items():
            if key in external_layers.keys():
                total_shared += size

        return total_shared

class DistanceMatrix(object):
    '''Sorts images by highest amount of shared data'''

    def __init__(self):
        self.__shared_data = {}
        self.__images = {}

    def add_image(self, docker_image):
        for name, image in self.__images.items():
            if name not in self.__shared_data.keys():
                self.__shared_data.setdefault(name, {})
            self.__shared_data[name][docker_image.full_name()] = docker_image.shared_data(image)

        self.__images[docker_image.full_name()] = docker_image

    def get_image_list(self):
        return self.__images.values()

    def get_closest_to(self, docker_image, skip_list=[]):

        current_max = 0
        closest = None
        for image_name, pairs in self.__shared_data.items():
            if docker_image.full_name() != image_name and docker_image.full_name() in pairs.keys():
                if image_name in skip_list:
                    continue
                elif pairs[docker_image.full_name()] > current_max:
                    current_max = pairs[docker_image.full_name()]
                    closest = self.__images[image_name]
            elif docker_image.full_name() == image_name:
                for second_image_name in pairs.keys():
                    if second_image_name in skip_list:
                        continue
                    elif pairs[second_image_name] > current_max:
                        current_max = pairs[second_image_name]
                        closest = self.__images[second_image_name]

        return closest



class AccumulatedUsage(object):

    def __init__(self):
        self.__layers = {}
        self.__used = 0.0

    def contains_layer(self, layer_digest):
        return layer_digest in self.__layers.keys()

    def add(self, docker_image):

        new_layers = docker_image.get_layers()

        for digest, size in new_layers.items():
            if not self.contains_layer(digest):
                self.__used += size
                self.__layers[digest] = size


    def get_current_usage(self):
        return self.__used
