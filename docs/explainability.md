# Grad-CAM explainability

`generate_gradcam` loads the saved classifier and applies the same EXIF-aware image preprocessing used by inference. It captures the final EfficientNet B0 feature block (`features[-1]`), averages gradients spatially to weight feature channels, applies ReLU, normalizes the resulting map, and resizes it to the original oriented image dimensions. The service returns the predicted class, confidence, class probabilities, heatmap, and blended overlay.

Grad-CAM visualizes activation gradients for the model's predicted class. It does not prove biological causation, establish that a highlighted area is diseased, or replace expert diagnosis. Image backgrounds or dataset shortcuts can influence the map.

`python -m scripts.smoke_gradcam` exercises the function on a real PlantVillage file and saves the heatmap/overlay under `reports/explainability/smoke/`. In the recorded one-epoch smoke-model run, a PlantVillage `Tomato_healthy` sample was predicted as `tomato_bacterial_spot` at confidence 0.1889. This is a pipeline check from a weak smoke model, not a meaningful disease prediction. The prediction and map used the same class, and both output images matched the oriented input dimensions (256×256).
