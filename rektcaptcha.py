import math

import torch


class Rekt:
    def __init__(self):
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5l", pretrained=True)
        self.names = self.model.names

    def inference(self, img, max_column):
        results = []
        inferesult = self.model(img)
        xy_result = inferesult.xyxy[0]

        for it_result in xy_result:
            class_name = self.names[int(it_result[5])]
            # 95 and 125 are tile size
            if max_column == 3:
                tile_column = math.ceil(float(it_result[0]) / 125.0)
                tile_row = math.ceil(float(it_result[1]) / 125.0)
            elif max_column == 4:
                tile_column = math.ceil(float(it_result[0]) / 95.0)
                tile_row = math.ceil(float(it_result[1]) / 95.0)
            results.append(
                {
                    "tile_column": tile_column,
                    "tile_row": tile_row,
                    "confident": float(it_result[4]),
                    "class": class_name,
                }
            )
        return results
