import numpy as np
import glob

import my_util



def run_APSP_diag_iteration(q, q_, p, rdd_partitioner, apsp_graph, BLOCKS_DIR, sc):

    def doPhase1(x, q_):
        ((I_, J_), thisBlock) = x
        diagBlock = my_util.scipy_floyd(thisBlock)
        (shape1, shape2) = map(str, diagBlock.shape)
        blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(q_)+'_'+str(q_)+'_'+shape1+'_'+shape2+'.csv'
        return ((I_, J_), diagBlock)


    def doPhase2(x, q_):
        ((I_, J_), thisBlock) = x
        blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(q_)+'_'+str(q_)+'_*.csv'
        blkfname = glob.glob(blkfname)
        blkfname = blkfname[0]
        bsize = tuple(map(int, blkfname.split('/')[-1].split('.')[0].split('_')[-2:]))
        diagPass = np.memmap(blkfname, shape=bsize, dtype='float', mode='r')

        if J_ == q_:
            updateP1 = my_util.minmpmatmul(thisBlock, diagPass, thisBlock)
        else:
            updateP1 = my_util.minmpmatmul(diagPass, thisBlock, thisBlock)
        return ((I_, J_), updateP1)

    def doPhase3(x, q_):
        ((I_, J_), thisBlock) = x
        if I_ < q_:
            blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(I_)+'_'+str(q_)+'_*.csv'
            blkfname = glob.glob(blkfname)[0]
            bsize = tuple(map(int, blkfname.split('/')[-1].split('.')[0].split('_')[-2:]))
            blk_L = np.memmap(blkfname, shape=bsize, dtype='float', mode='r')
        else:
            blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(q_)+'_'+str(I_)+'_*.csv'
            blkfname = glob.glob(blkfname)[0]
            bsize = tuple(map(int, blkfname.split('/')[-1].split('.')[0].split('_')[-2:]))
            blk_L = np.memmap(blkfname, shape=bsize, dtype='float', mode='r').transpose()
        if q_ < J_:
            blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(q_)+'_'+str(J_)+'_*.csv'
            blkfname = glob.glob(blkfname)[0]
            bsize = tuple(map(int, blkfname.split('/')[-1].split('.')[0].split('_')[-2:]))
            blk_R = np.memmap(blkfname, shape=bsize, dtype='float', mode='r')
        else:
            blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(J_)+'_'+str(q_)+'_*.csv'
            blkfname = glob.glob(blkfname)[0]
            bsize = tuple(map(int, blkfname.split('/')[-1].split('.')[0].split('_')[-2:]))
            blk_R = np.memmap(blkfname, shape=bsize, dtype='float', mode='r').transpose()

        thisBlock = my_util.minmpmatmul(blk_L, blk_R, thisBlock)
        return ((I_, J_), thisBlock)


    diagBlock1 = apsp_graph.filter(lambda x : x[0][0] == q_ and x[0][1] == q_)\
                          .map(lambda x : doPhase1(x, q_), preservesPartitioning=False)

    diagBlock = diagBlock1.collectAsMap()
    diagBlock = diagBlock[(q_, q_)]

    (shape1, shape2) = map(str, diagBlock.shape)
    blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(q_)+'_'+str(q_)+'_'+shape1+'_'+shape2+'.csv'

    diagBlock.saveAsTextFile(blkfname)

    rowColBlocksRDD = apsp_graph.filter(lambda x : (x[0][0] == q_) ^ (x[0][1] == q_))\
                            .map(lambda x : doPhase2(x, q_), preservesPartitioning=False)

    rowColBlocks = rowColBlocksRDD.collectAsMap()
    for i, j in rowColBlocks:
        shape1, shape2 = map(str, rowColBlocks[(i,j)].shape)
        blkfname = BLOCKS_DIR+'block_q'+str(q_)+'_'+str(i)+'_'+str(j)+'_'+shape1+'_'+shape2+'.csv'
        rowColBlocks[(i,j)].saveAsTextFile(blkfname)


    p3Blocks = apsp_graph.filter(lambda x : x[0][0] != q_ and x[0][1] != q_)\
                        .map(lambda x : doPhase3(x, q_), preservesPartitioning=False)
    # UNION (phase2 p3Blocks) AS phase3 and update/compute


    apsp_graph = sc.union([diagBlock1, rowColBlocksRDD, p3Blocks])\
                  .partitionBy(p, rdd_partitioner)

    # RESET apspGraph = phase3 (result after update / computation)
    return apsp_graph


def collect_bc_block_fw(apsp_graph, q, p, rdd_partitioner, BLOCKS_DIR, sc):

    for q_ in range(0, q, 1):
        apsp_graph = run_APSP_diag_iteration(q, q_, p, rdd_partitioner, apsp_graph, BLOCKS_DIR, sc)

    return apsp_graph
