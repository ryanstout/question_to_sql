# Wrapper around Faiss library for building and querying ANN indexes
import numpy as np
import time
import faiss


class AnnFaiss():
    def build_and_save(self, data, output_path, dimensions=1536):
        t1 = time.time()

        print(f"Build Faiss: {data.shape} - {data.dtype}")
        # index_type = 'OPQ64_256,Residual2x14,PQ64'
        # index_type = "IVF10,PQ256x8"
        # index_type = 'PQ256x8'
        # index_type = 'PQ256x10'
        index_type = "IVF50,PQ256x8"  # 28Mb, good
        # index_type = "OPQ16,PQ256x8" # 28Mb, good
        # index_type = 'PCAR640,SQ8' # pretty good, 75mb
        # index_type = 'SQ8'
        # index_type = 'Flat' # brute force (exaustive nearest neighbor search)

        # self.index = faiss.index_factory(
        #     1280, index_type, faiss.METRIC_INNER_PRODUCT)
        # self.index = faiss.index_factory(
        #     dimensions, "IVF10,PQ16x8", faiss.METRIC_INNER_PRODUCT)

        rows = data.shape[0]
        if dimensions < 1000:
            self.index = faiss.IndexFlatIP(dimensions)
        else:
            quantizer = faiss.IndexFlatL2(dimensions)
            self.index = faiss.IndexIVFFlat(
                quantizer, dimensions, min(1000, rows), faiss.METRIC_INNER_PRODUCT)
            self.index.nprobe = 10

        # nlist = 20
        # m = 8
        # quantizer = faiss.IndexFlatL2(1280)  # this remains the same
        # self.index = faiss.IndexIVFPQ(quantizer, 1280, nlist, m, 8)
        print("Normalizing...")
        faiss.normalize_L2(data)

        print("Training...")
        self.index.train(data)
        print("Building index...")
        self.index.add(data)

        faiss.write_index(self.index, output_path + '.faiss')

        t2 = time.time()
        print("Built Faiss in ", t2 - t1, " secs")

    def load(self, faiss_path, nprobe=15):
        self.index = faiss.read_index(faiss_path + '.faiss')

        # Set how many lists to look for NN in
        self.index.nprobe = nprobe
        self.nprobe = nprobe
        # index_ivf = faiss.extract_index_ivf(self.index)
        # index_ivf.nprobe = 6

        # ParameterSpace().set_index_parameter(self.index, "nprobe", 6)

    def query(self, query, number_of_matches):
        t1 = time.time()
        query = np.expand_dims(query, axis=0)
        faiss.normalize_L2(query)
        scores, indexes = self.index.search(query, number_of_matches)
        t2 = time.time()
        print("Query NN in: ", indexes.shape, ' in ',
              t2 - t1, ' (nprobe ', self.nprobe, ')')

        return indexes[0]