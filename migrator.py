from registry import Registry
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

    # loop through registry's images
    # or through the ones given in command line
    for image_name in image_list:
        print "# Image: {}".format(image_name)


        tags_list = registry.list_tags(image_name)

        if tags_list == None or tags_list == []:
            print "#  no tags!"
            continue

        if image_name in images_to_skip:
            print "# skipping all tags for image..."
            continue

        # print commands for transfer
        for tag in tags_list:
            if "{}:{}".format(image_name,tag) in images_to_skip:
                print "# skipping tag {} for image {}".format(tag, image_name)
                break

            print "docker pull {}/{}:{}".format(origin_host_no_http, image_name, tag)
            print "docker tag {}/{}:{} {}/{}:{}".format(origin_host_no_http, image_name, tag,
                                                        dest_host_no_http, image_name, tag)
            print "docker push {}/{}:{}".format(dest_host_no_http, image_name, tag)
            print "echo '{}:{}' >> migration.done".format( image_name, tag)
            print "\n\n"




if __name__ == "__main__":
    args = parse_args()
    try:
        main_loop(args)
    except KeyboardInterrupt:
        print "Ctrl-C pressed, quitting"
        exit(1)