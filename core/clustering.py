import numpy as np
from shapely.geometry import shape
from sklearn.cluster import DBSCAN


class GeoClusterer:
    """
    Experimental module:
    spatial clustering using DBSCAN.
    """

    def __init__(self, eps=0.01, min_samples=2):
        self.eps = eps
        self.min_samples = min_samples

    def extract_centroids(self, features):
        points = []

        for feature in features:
            geom = shape(feature["geometry"])
            centroid = geom.centroid

            points.append([centroid.x, centroid.y])

        return np.array(points)

    def cluster(self, features):
        coords = self.extract_centroids(features)

        if len(coords) == 0:
            return []

        model = DBSCAN(eps=self.eps, min_samples=self.min_samples)

        labels = model.fit_predict(coords)

        clustered = []

        for feature, label in zip(features, labels):
            feature_copy = feature.copy()

            feature_copy["properties"] = feature_copy.get("properties", {}).copy()
            feature_copy["properties"]["cluster_id"] = int(label)

            clustered.append(feature_copy)

        return clustered
