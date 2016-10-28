from registry import Registry
from Image import DockerImage, DistanceMatrix, AccumulatedUsage

import argparse
import os.path

def parse_args():
    parser = argparse.ArgumentParser(
        description="List or delete images from Docker registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("""
IMPORTANT: after removing the tags, run the garbage collector
           on your registry host:

   docker-compose -f [path_to_your_docker_compose_file] run \\
       registry bin/registry garbage-collect \\
       /etc/docker/registry/config.yml

or if you are not using docker-compose:

   docker run registry:2 bin/registry garbage-collect \\
       /etc/docker/registry/config.yml

for more detail on garbage collection read here:
   https://docs.docker.com/registry/garbage-collection/
                """))
    parser.add_argument(
        '-l','--login',
        help="Login and password to access to docker registry",
        required=False,
        metavar="USER:PASSWORD")

    parser.add_argument(
        '-d', '--destination',
        help="Hostname for destination registry server, e.g. https://example.com:5000",
        required=True,
        metavar="URL")

    parser.add_argument(
        '-o', '--origin',
        help="Hostname for source registry server, e.g. https://example.com:5000",
        required=True,
        metavar="URL")

    parser.add_argument(
        '--dry-run',
        help=('If used in combination with --delete,'
              'then images will not be deleted'),
        action='store_const',
        default=False,
        const=True)

    parser.add_argument(
        '-i','--image',
        help='Specify images and tags to list/delete',
        nargs='+',
        metavar="IMAGE:[TAG]")

    parser.add_argument(
        '-s', '--skip',
        help='Specify images and tags to skip in the migration',
        required=False,
        default=None
    )

    parser.add_argument(
        '-m', '--max_space_use',
        help='Specify maximum amount of disk space to be used, default (0) is unlimited',
        type=float,
        required=False,
        default=0
    )


    parser.add_argument(
        '--layers',
        help=('Show layers digests for all images and all tags'),
        action='store_const',
        default=False,
        const=True)


    return parser.parse_args()

def main_loop(args):


    registry = Registry(args.origin, args.login)

    if args.image != None:
        image_list = args.image
    else:
        image_list = registry.list_images()

    images_to_skip = []
    if args.skip != None and os.path.isfile(args.skip):
        sf = open(args.skip, mode='r')
        images_to_skip = sf.read().splitlines()

    origin_host_no_http = args.origin.replace('http://', '').replace('https://', '')
    dest_host_no_http = args.destination.replace('http://', '').replace('https://', '')

    dist_matrix = DistanceMatrix()

    for image_name in image_list:
        tags_list = registry.list_tags(image_name)

        if tags_list == None or tags_list == []:
            continue

        if image_name in images_to_skip:
            print "# skipping all tags for image {}".format(image_name)
            continue

        for tag in tags_list:
            if "{}:{}".format(image_name, tag) in images_to_skip:
                print "# skipping tag {} for image {}".format(tag, image_name)
                break

            image_obj = DockerImage(image_name, tag)
            for layer in registry.list_tag_layers(image_name,tag):
                image_obj.add_layer(digest=layer['digest'], size=layer['size'])
            dist_matrix.add_image(image_obj)

    image_obj_list = dist_matrix.get_image_list()
    image_obj_list.sort(key=lambda x: len(x.get_layers().keys()), reverse=True)

    accumulator = AccumulatedUsage()

    next_image = image_obj_list[1]
    visited_images = []
    done = 0

    while next_image is not None:
        image_name = next_image.full_name()
        print "# Image: {}".format(image_name)
        print "# Size: {}".format(next_image.get_size())
        print "docker pull {}/{}".format(origin_host_no_http, image_name)
        print "docker tag {}/{} {}/{}".format(origin_host_no_http, image_name,
                                                    dest_host_no_http, image_name)
        print "docker push {}/{}".format(dest_host_no_http, image_name)
        print "echo '{}' >> migration.done".format(image_name)
        print "\n\n"

        visited_images.append(image_name)
        accumulator.add(next_image)

        current_usage = accumulator.get_current_usage()
        done += 1
        print "# current usage: {} MBs".format(current_usage)
        if 0 < args.max_space_use < accumulator.get_current_usage():
            print "# Used so far {} GBs, above limit of {}".format(current_usage/(1024**3), args.max_space_use/(1024**3))
            print "# Going to delete existing docker images"
            print "# Done so far {} out of {}".format(done, len(image_obj_list))
            print "docker rm $(docker ps -a -q)"
            print "docker rmi $(docker images -q)"
            print "docker rmi -f $(docker images | grep 'docker-registry' | awk '{ print $3 }' | sort -u)"
            print "#\n#"
            accumulator = AccumulatedUsage()


        next_image = dist_matrix.get_closest_to(next_image, skip_list=visited_images)






if __name__ == "__main__":
    args = parse_args()
    try:
        main_loop(args)
    except KeyboardInterrupt:
        print "Ctrl-C pressed, quitting"
        exit(1)