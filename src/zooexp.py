from main import KernelPheno

import os.path as osp
import click
import json
from datetime import datetime as dt

import pandas as pd


@click.command()
@click.argument(
    'export'
)
@click.option(
    '-o',
    'output',
    help='Path to the ouput file',
    default='../data'
)
def zooexp(export, output):

    # load all data
    try:
        data = pd.read_csv(export)
    except FileNotFoundError as fnfe:
        log.info("Could not find export file.")
        log.info(fnfe.output)
        exit(-1)

    target = data[['annotations', 'subject_data']]

    # get filenames
    target = target.assign(
                    filename=target['subject_data']\
                            .apply(_get_img_name))
    # get kernel ratings
    target = target.assign(
        ratings=target['annotations'].apply(_get_kernel_ratings)
    )

    target = target.assign(
        num_ratings=target.apply(
            lambda row: _recursive_len(row['ratings']), axis=1
        )
    )

    # get bounding boxes
    target = target.assign(
        bounding_boxes=target['annotations'].apply(_get_bounding_boxes)
    )

    # count number of bounding boxes
    target = target.assign(
        num_bboxes=target.apply(lambda row: len(row['bounding_boxes']), axis=1)
    )

    # get kernel object counts
    target = target.assign(
        num_objects=target.apply(_get_cmp_kernel_count, axis=1)
    )

    # sort by filename
    target = target.sort_values('filename', kind='mergesort')

    # output report
    final_inds = ['filename',
                  'num_ratings',
                  'num_bboxes',
                  'num_objects',
                  'ratings',
                  'bounding_boxes']

    target[final_inds].to_csv(
        osp.join(output, "report_" + dt.now().strftime("%m-%d-%y:%X") + ".csv")
    )

    return

KernelPheno.add_command(zooexp)

def _get_img_name(subject_data_entry):
    subject_data = json.loads(subject_data_entry)
    # peel away data structure layers and return
    return list(subject_data.values()).pop()['Filename']


def _get_kernel_ratings(annotation_data_entry):
    anno_data = json.loads(annotation_data_entry)
    for anno in anno_data:
        # The kernel ratings task is T1
        if anno['task'] == 'T1':
            return _listify_csv(anno['value'])

    return []


def _listify_csv(csv_str):
    if csv_str == "":
        return []
    split_on_newline = csv_str.strip().split("\n")
    listed = []
    for line in split_on_newline:
        listed.append(line.split(","))
    return listed


def _get_bounding_boxes(annotation_data_entry):
    anno_data = json.loads(annotation_data_entry)
    for anno in anno_data:
        if anno['task'] == 'T2':
            bboxes = []
            for box_i in anno['value']:
                bboxes.append({
                    'x': round(box_i['x']),
                    'y': round(box_i['y']),
                    'x_offset': round(box_i['width']),
                    'y_offset': round(box_i['height'])
                })
            return bboxes
    return []


def _get_cmp_kernel_count(ratings_bboxes_entry):
    if _recursive_len(ratings_bboxes_entry['ratings']) == len(ratings_bboxes_entry['bounding_boxes']):
        return len(ratings_bboxes_entry['bounding_boxes'])
    else:
        return -1


def _recursive_len(item):
    ''' https://stackoverflow.com/questions/27761463/how-can-i-get-the-total-number-of-elements-in-my-arbitrarily-nested-list-of-list '''
    if type(item) == list:
        return sum(_recursive_len(subitem) for subitem in item)
    elif item == None:
        return 0
    else:
        return 1


def _set_err_msg(annotation_entry):
    '''
    Not being used
    '''
    # It might be an old annotation with task 'T0'
    # check and return a message
    if len(annotation_entry) == 1 and 'T0' == annotation_entry.pop()['task']:
        return 'OLD_ANNOTATION_TASK'
    else:
        return 'UNKOWN_ERROR'


if __name__ == '__main__':

    import sys

    if len(sys.argv) == 2:
        zooexp(sys.argv[1])
    else:
        zooexp("/home/apages/pysrc/KernelPheno/data/sample_zoo_export.csv")
