
## User Guide

`APSPark` is executed by calling `APSPark.py`. The software requires additional modules that are part of the source code. The easiest way to provide these modules to Spark is by first calling `pack.sh` (one time effort to produce `APSPark.zip`), and then adding `--py-files /path/to/APSPark.zip` to `spark-submit`. Additionally, the following Python modules must be available: `numba`, `numpy` and `scipy`. Please note that for the best performance, these modules should be configured to work with a high performance BLAS library (for example, Intel MKL).

`APSPark` supports the following command line options:

* `-n` number of vertices in the input graph 
* `-b` block size for adjacency matrix decomposition
* `-p` number of Spark RDD partitions to store adjacency matrix
* `-F` RDD partitioner (use `md` for custom multi-diagonal partitioner, or `ph` for the default Spark partitioner)
* `-S` solver type (use `im` for in-memory solver, or `cb` for collect-broadcast via persistent storage)
* `-f` input graph (`tsv` format: `source target weight`)
* `-o` output folder

Please refer to the original `APSPark` paper [1] if the meaning of the options is not clear.

##### Example invocation

`spark-submit --py-files ./APSPark.zip ./APSPark.py -n 8192 -b 1024 -p 16 -F md -S im -f data/er8K-0.01.txt -o out
`
The above invocation will execute Blocked-IM approach using multi-diagonal partitioner on our toy example data `er8K-0.01.txt` with 8192 nodes. The result will be stored in `out` folder.

When calling `APSPark` with the `cb` solver, for example:

`spark-submit --py-files ./APSPark.zip ./APSPark.py -n 8192 -b 1024 -p 16 -F md -S cb -f data/er8K-0.01.txt -o out
`
the current working directory must be a shared file system, i.e., all nodes is the executing Spark cluster must be able to read/write to that directory.