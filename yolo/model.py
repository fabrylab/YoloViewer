import tensorflow as tf
import numpy as np



def build_net(model_path,H,W, downsamples):
    input_tensor = tf.keras.Input((H,W,3), name="Image")
    #net = tf.keras.applications.MobileNetV2(input_tensor=input_tensor,
    net = tf.keras.applications.efficientnet.EfficientNetB0(input_tensor=input_tensor,
                                                            include_top=False,
                                                            weights='imagenet',
                                                            pooling=None,
                                                           )
    yolos = {}
    _, netH, netW, netF = net.output.shape
    nFilters = 6
    key = "yolo%03d"
    for d in downsamples:
        targetH, targetW = H//d, W//d

        if (netH>=targetH):
            kH = int(netH/targetH)
            kW = int(netW/targetW)
            tensorH, tensorW = netH//kH, netW//kW
        else:
            kH = int(targetH/netH)
            kW = int(targetW/netW)
            tensorH, tensorW = netH*kH, netW*kW

        if tensorW != targetW:
            convName=None
            hName=None
            wName=key%d
        elif tensorH != targetH:
            convName=None
            hName=key%d
            wName=None
        else:
            convName=key%d
            hName=None
            wName=None

        if (netH>=targetH):
            conv = tf.keras.layers.Conv2D(name=convName, kernel_size=(kH, kW),
                                                       strides=(kH, kW), filters=nFilters, activation="sigmoid",
                                                       kernel_regularizer=None,
                                                       bias_regularizer=None,
                                                       activity_regularizer=None,
                                                       )(net.output)
        else:
            conv = tf.keras.layers.Conv2DTranspose(name=convName, kernel_size=(kH, kW),
                                                       strides=(kH, kW), filters=nFilters, activation="sigmoid",
                                                       kernel_regularizer=None,
                                                       bias_regularizer=None,
                                                       activity_regularizer=None,
                                                       )(net.output)

        if tensorH>targetH:
            cH = tensorH-targetH
            postH = tf.keras.layers.Cropping2D(name=hName, cropping=((cH//2, cH - cH//2), (0, 0)))(conv)
        elif tensorH<targetH:
            cH = targetH-tensorH
            postH = tf.keras.layers.ZeroPadding2D(name=hName, padding=((cH//2, cH - cH//2), (0, 0)))(conv)
        else:
            postH = conv

        if tensorW>targetW:
            cW = tensorW-targetW
            postW = tf.keras.layers.Cropping2D(name=wName, cropping=((0, 0), (cW//2, cW-cW//2)))(postH)
        elif tensorW<targetW:
            cW = targetW-tensorW
            postW = tf.keras.layers.ZeroPadding2D(name=wName, padding=((0, 0), (cW//2, cW-cW//2)))(postH)
        else:
            postW = postH

        yolos[key%d] = postW
        print(targetH, targetW, tensorH, tensorW, postW.shape)
    model = tf.keras.Model(inputs=net.input, outputs=yolos.values())
    model.load_weights(model_path)

    return model

def predict(model, stack, th,downsamples,anchorOverlap):
    pred = model(stack)
    print(pred[0][pred[0][...,0]>0.5].shape)
    anchorLevelIds = np.concatenate(
        [np.ones((p[..., 0] > th).numpy().sum(), dtype=int) * i for i, p in enumerate(pred)])
    imageId, yId, xId = np.concatenate([tf.where(p[..., 0] > th).numpy() for p in pred], axis=0).T
    c, x, y, w, h, p = np.concatenate([p[p[..., 0] > th].numpy() for p in pred], axis=0).T
    anchorSizes = downsamples[anchorLevelIds]
    X = (xId + x) * anchorSizes
    Y = (yId + y) * anchorSizes
    W = w * anchorSizes / anchorOverlap
    H = h * W
    angle = p * 180

    # with timer("NMS"):
    NMSthreshold = 1
    distN = ((X[:, None] - X[None, :]) ** 2 + (Y[:, None] - Y[None, :]) ** 2) / (W[:, None] * W[None, :])
    NM = ((NMSthreshold * tf.eye(len(X)) + distN) < NMSthreshold) & (c[:, None] < c[None, :]) & (
            imageId[:, None] == imageId[None, :])
    # with timer("export to numpy"):
    all_data = np.stack([X, Y, W, H, angle, imageId]).T[~np.any(NM, axis=1)]
    return  all_data

