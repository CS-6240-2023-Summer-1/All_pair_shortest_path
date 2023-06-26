import numpy as np

# initialize upper-tri block mtx using params
def initialize_blocks(n, b, q, p, rdd_partitioner, sc):

    def sendBlkToBlk(x):
        (blkId, blkCnt) = x
        for i in range(0, q, 1):
            yield(tuple(sorted((blkId, i))), (blkCnt, blkId))

    def doBlock(iter_):
        for ((I_, J_), _LIST_) in iter_:
            if len(_LIST_) == 1:
                THEBLOCK = np.inf * np.ones((_LIST_[0][0], _LIST_[0][0]))
                np.fill_diagonal(THEBLOCK, 0.)
                yield((I_, J_), THEBLOCK)
            elif _LIST_[0][1] < _LIST_[1][1]:
                yield((I_, J_), np.inf * np.ones((_LIST_[0][0], _LIST_[1][0])))
            else:
                yield((I_, J_), np.inf * np.ones((_LIST_[1][0], _LIST_[0][0])))

    init_blocks = sc.parallelize([i for i in range(n)], numSlices=p)\
                   .map(lambda x : (x // b, x))\
                   .combineByKey((lambda x : 1),\
                                 (lambda x, y : x + 1),\
                                 (lambda x, y : x + y))\
                   .flatMap(lambda x : sendBlkToBlk(x))\
                   .combineByKey((lambda x : [x]),\
                                  (lambda x, y : x + [y]),\
                                  (lambda x, y : x + y),
                                   numPartitions=p,
                                   partitionFunc=rdd_partitioner)\
                   .mapPartitions(lambda x : doBlock(x),\
                                   preservesPartitioning=False)
    return init_blocks


def fill_blocks(b, input_file, init_blocks, p, rdd_partitioner, sc):

    def edgeToBlock(x):
        i, j, val = x.rstrip().split()

        i = int(i)
        j = int(j)

        if i > j:
            i, j = j, i

        I = i // b
        J = j // b
        loc_i = i % b
        loc_j = j % b

        yield ((I, J), (loc_i, loc_j, float(val)))
        if (I == J): yield ((I, J), (loc_j, loc_i, float(val)))

    edge_list = sc.textFile(input_file, minPartitions=p)\
                 .flatMap(lambda x : edgeToBlock(x))

    def matComb(x):
        if isinstance(x, np.ndarray):
            return x
        else: return [x]

    def updateMatList(M_, L_):
        r_i, c_j, d_v = zip(*L_)
        M_[r_i, c_j] = d_v
        return M_

    def mergeMat(x, y):
        if isinstance(x, np.ndarray):
            return updateMatList(x, [y])
        if isinstance(y, np.ndarray):
            return updateMatList(y, x)
        return [y] + x

    def mergeMatComb(x, y):
        if isinstance(x, np.ndarray):
            return updateMatList(x, y)
        if isinstance(y, np.ndarray):
            return updateMatList(y, x)
        return y + x

    filled_blocks = init_blocks.union(edge_list)\
                   .combineByKey(\
                    (lambda x : matComb(x)),\
                    (lambda x, y : mergeMat(x, y)),\
                    (lambda x, y : mergeMatComb(x, y)),\
                    numPartitions=p,\
                    partitionFunc=rdd_partitioner)
    return filled_blocks
