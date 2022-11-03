function Transform() {
    this.x = 0;
    this.y = 0;
    this.scale = 1;
    this.rotation = 0;
}

function makeSvgController(svgElement) {

    var owner = svgElement.ownerSVGElement
    if (!owner) {
        throw new Error(
            'Do not apply panzoom to the root <svg> element. ' +
            'Use its child instead (e.g. <g></g>). ' +
            'As of March 2016 only FireFox supported transform on the root element')
    }

    var api = {
        getBBox: getBBox,
        getWidth: getOwnerWidth,
        getHeight: getOwnerHeight,
        getScreenCTM: getScreenCTM,
        getOwner: getOwner,
        applyTransform: applyTransform,
        initTransform: initTransform
    }

    return api

    function getOwner() {
        return owner
    }

    function getBBox() {
        var bbox = svgElement.getBBox()
        return {
            left: bbox.x,
            top: bbox.y,
            width: bbox.width,
            height: bbox.height,
        }
    }

    function getOwnerWidth() {
        return svgElement.ownerSVGElement.width.baseVal.value;
    }

    function getOwnerHeight() {
        return svgElement.ownerSVGElement.height.baseVal.value;
    }

    function getScreenCTM() {
        var ctm = owner.getCTM();
        if (!ctm) {
            // This is likely firefox: https://bugzilla.mozilla.org/show_bug.cgi?id=873106
            // The code below is not entirely correct, but still better than nothing
            return owner.getScreenCTM();
        }
        return ctm;
    }

    function initTransform(transform) {
        var screenCTM = svgElement.getCTM()
        transform.x = screenCTM.e;
        transform.y = screenCTM.f;
        transform.scale = screenCTM.a;
        owner.removeAttributeNS(null, 'viewBox');
    }

    function applyTransform(transform) {
        let a = transform.scale * Math.cos(transform.rotation * Math.PI / 180);
        let b = transform.scale * Math.sin(transform.rotation * Math.PI / 180);
        let _b = -b;
        svgElement.setAttribute('transform', 'matrix(' +
            a + ' ' + _b + ' ' +
            b + ' ' + a + ' ' +
            // transform.scale + ' 0 0 ' +
            // transform.scale + ' ' +
            transform.x + ' ' + transform.y + ')')
    }
}


var defaultZoomSpeed = 1;
var defaultDoubleTapZoomSpeed = 1.75;
var doubleTapSpeedInMS = 300;

/**
 * Creates a new instance of panzoom, so that an object can be panned and zoomed
 *
 * @param {DOMElement} domElement where panzoom should be attached.
 * @param {Object} options that configure behavior.
 */
function createPanZoom(domElement, options) {
    options = options || {};

    var panController = makeSvgController(domElement, options);

    var owner = panController.getOwner();
    // just to avoid GC pressure, every time we do intermediate transform
    // we return this object. For internal use only. Never give it back to the consumer of this library
    var storedCTMResult = {x: 0, y: 0};

    var isDirty = false;
    var transform = new Transform();

    if (panController.initTransform) {
        panController.initTransform(transform);
    }

    var filterKey = typeof options.filterKey === 'function' ? options.filterKey : noop;
    // TODO: likely need to unite pinchSpeed with zoomSpeed
    var pinchSpeed = typeof options.pinchSpeed === 'number' ? options.pinchSpeed : 1;
    var bounds = options.bounds;
    var maxZoom = typeof options.maxZoom === 'number' ? options.maxZoom : Number.POSITIVE_INFINITY;
    var minZoom = typeof options.minZoom === 'number' ? options.minZoom : 0;

    var boundsPadding = typeof options.boundsPadding === 'number' ? options.boundsPadding : 0.05;
    var zoomDoubleClickSpeed = typeof options.zoomDoubleClickSpeed === 'number' ? options.zoomDoubleClickSpeed : defaultDoubleTapZoomSpeed;
    var beforeWheel = options.beforeWheel || noop;
    var beforeMouseDown = options.beforeMouseDown || noop;
    var speed = typeof options.zoomSpeed === 'number' ? options.zoomSpeed : defaultZoomSpeed;
    var transformOrigin = parseTransformOrigin(options.transformOrigin);

    validateBounds(bounds);


    var frameAnimation;
    var lastTouchEndTime = 0;
    var lastSingleFingerOffset;
    var touchInProgress = false;

    // We only need to fire panstart when actual move happens
    var panstartFired = false;

    // cache mouse coordinates here
    var mouseX;
    var mouseY;

    var pinchZoomLength;

    var smoothScroll;
    if ('smoothScroll' in options && !options.smoothScroll) {
        // If user explicitly asked us not to use smooth scrolling, we obey
        smoothScroll = rigidScroll();
    } else {
        // otherwise we use forward smoothScroll settings to kinetic API
        // which makes scroll smoothing.
        smoothScroll = kinetic(getPoint, scroll, options.smoothScroll);
    }

    var moveByAnimation;
    var zoomToAnimation;

    var multiTouch;
    var paused = false;

    listenForEvents();

    var api = {
        dispose: dispose,
        moveBy: internalMoveBy,
        moveTo: moveTo,
        centerOn: centerOn,
        zoomTo: publicZoomTo,
        zoomAbs: zoomAbs,
        smoothZoom: smoothZoom,
        smoothZoomAbs: smoothZoomAbs,
        // showRectangle: showRectangle,
        rotate: rotate,
        fitToView: fitToView,
        fitToPixel: fitToPixel,

        pause: pause,
        resume: resume,
        isPaused: isPaused,

        getTransform: getTransformModel,

        getMinZoom: getMinZoom,
        setMinZoom: setMinZoom,

        getMaxZoom: getMaxZoom,
        setMaxZoom: setMaxZoom,

        getTransformOrigin: getTransformOrigin,
        setTransformOrigin: setTransformOrigin,

        getZoomSpeed: getZoomSpeed,
        setZoomSpeed: setZoomSpeed
    };

    eventify(api);

    return api;

    function pause() {
        releaseEvents();
        paused = true;
    }

    function resume() {
        if (paused) {
            listenForEvents();
            paused = false;
        }
    }

    function isPaused() {
        return paused;
    }

    function transformToScreen(x, y) {
        if (panController.getScreenCTM) {
            var parentCTM = panController.getScreenCTM();
            var parentScaleX = parentCTM.a;
            var parentScaleY = parentCTM.d;
            var parentOffsetX = parentCTM.e;
            var parentOffsetY = parentCTM.f;
            storedCTMResult.x = x * parentScaleX - parentOffsetX;
            storedCTMResult.y = y * parentScaleY - parentOffsetY;
        } else {
            storedCTMResult.x = x;
            storedCTMResult.y = y;
        }

        return storedCTMResult;
    }

    function getTransformModel() {
        // TODO: should this be read only?
        return transform;
    }

    function getMinZoom() {
        return minZoom;
    }

    function setMinZoom(newMinZoom) {
        minZoom = newMinZoom;
    }

    function getMaxZoom() {
        return maxZoom;
    }

    function setMaxZoom(newMaxZoom) {
        maxZoom = newMaxZoom;
    }

    function getTransformOrigin() {
        return transformOrigin;
    }

    function setTransformOrigin(newTransformOrigin) {
        transformOrigin = parseTransformOrigin(newTransformOrigin);
    }

    function getZoomSpeed() {
        return speed;
    }

    function setZoomSpeed(newSpeed) {
        if (!Number.isFinite(newSpeed)) {
            throw new Error('Zoom speed should be a number');
        }
        speed = newSpeed;
    }

    function getPoint() {
        return {
            x: transform.x,
            y: transform.y
        };
    }

    function moveTo(x, y) {
        transform.x = x;
        transform.y = y;

        keepTransformInsideBounds();

        triggerEvent('pan');
        makeDirty();
    }

    function moveBy(dx, dy) {
        moveTo(transform.x + dx, transform.y + dy);
    }

    function fitToView(width, height) {
        let svg_width = panController.getWidth();
        let svg_height = panController.getHeight();
        let svg_aspect = svg_width / svg_height;
        let img_aspect = width / height;
        console.log(svg_width, svg_height);
        console.log(width, height);
        // zoom to fit
        var scale = 1;
        if (svg_aspect > img_aspect) {
            scale = svg_height / height;
        } else {
            scale = svg_width / width;
        }
        zoomAbs(0, 0, scale);
        // move image center to canvas center
        var x = -width / 2 * scale;
        var y = -height / 2 * scale;
        var x_ = x * Math.cos(transform.rotation * Math.PI / 180) + y * Math.sin(transform.rotation * Math.PI / 180);
        var y_ = -x * Math.sin(transform.rotation * Math.PI / 180) + y * Math.cos(transform.rotation * Math.PI / 180);
        pz.moveTo(+x_ + svg_width / 2, y_ + svg_height / 2);
    }

    function fitToPixel() {
        let svg_width = panController.getWidth();
        let svg_height = panController.getHeight();
        var x = (transform.x - svg_width / 2) / transform.scale;
        var y = (transform.y - svg_height / 2) / transform.scale;
        // zoom to Pixel
        var scale = 1;
        zoomAbs(0, 0, scale);
        moveTo(+x + svg_width / 2, +y + svg_height / 2);
    }

    function rotate(angle) {
        let svg_width = panController.getWidth();
        let svg_height = panController.getHeight();
        var x = (transform.x - svg_width / 2);
        var y = (transform.y - svg_height / 2);
        transform.rotation = (transform.rotation + angle) % 360;
        var x_ = x * Math.cos(angle * Math.PI / 180) + y * Math.sin(angle * Math.PI / 180);
        var y_ = -x * Math.sin(angle * Math.PI / 180) + y * Math.cos(angle * Math.PI / 180);
        moveTo(+x_ + svgCanvas.width.baseVal.value / 2, +y_ + svgCanvas.height.baseVal.value / 2);
    }

    function keepTransformInsideBounds() {
        var boundingBox = getBoundingBox();
        if (!boundingBox) return;

        var adjusted = false;
        var clientRect = getClientRect();

        var diff = boundingBox.left - clientRect.right;
        if (diff > 0) {
            transform.x += diff;
            adjusted = true;
        }
        // check the other side:
        diff = boundingBox.right - clientRect.left;
        if (diff < 0) {
            transform.x += diff;
            adjusted = true;
        }

        // y axis:
        diff = boundingBox.top - clientRect.bottom;
        if (diff > 0) {
            // we adjust transform, so that it matches exactly our bounding box:
            // transform.y = boundingBox.top - (boundingBox.height + boundingBox.y) * transform.scale =>
            // transform.y = boundingBox.top - (clientRect.bottom - transform.y) =>
            // transform.y = diff + transform.y =>
            transform.y += diff;
            adjusted = true;
        }

        diff = boundingBox.bottom - clientRect.top;
        if (diff < 0) {
            transform.y += diff;
            adjusted = true;
        }
        return adjusted;
    }

    /**
     * Returns bounding box that should be used to restrict scene movement.
     */
    function getBoundingBox() {
        if (!bounds) return; // client does not want to restrict movement

        if (typeof bounds === 'boolean') {
            // for boolean type we use parent container bounds
            var ownerRect = owner.getBoundingClientRect();
            var sceneWidth = ownerRect.width;
            var sceneHeight = ownerRect.height;

            return {
                left: sceneWidth * boundsPadding,
                top: sceneHeight * boundsPadding,
                right: sceneWidth * (1 - boundsPadding),
                bottom: sceneHeight * (1 - boundsPadding)
            };
        }

        return bounds;
    }

    function getClientRect() {
        var bbox = panController.getBBox();
        var leftTop = client(bbox.left, bbox.top);

        return {
            left: leftTop.x,
            top: leftTop.y,
            right: bbox.width * transform.scale + leftTop.x,
            bottom: bbox.height * transform.scale + leftTop.y
        };
    }

    function client(x, y) {
        return {
            x: x * transform.scale + transform.x,
            y: y * transform.scale + transform.y
        };
    }

    function makeDirty() {
        isDirty = true;
        frameAnimation = window.requestAnimationFrame(frame);
    }

    function zoomByRatio(clientX, clientY, ratio) {
        if (isNaN(clientX) || isNaN(clientY) || isNaN(ratio)) {
            throw new Error('zoom requires valid numbers');
        }

        var newScale = transform.scale * ratio;

        if (newScale < minZoom) {
            if (transform.scale === minZoom) return;

            ratio = minZoom / transform.scale;
        }
        if (newScale > maxZoom) {
            if (transform.scale === maxZoom) return;

            ratio = maxZoom / transform.scale;
        }

        var size = transformToScreen(clientX, clientY);

        transform.x = size.x - ratio * (size.x - transform.x);
        transform.y = size.y - ratio * (size.y - transform.y);

        // TODO: https://github.com/anvaka/panzoom/issues/112
        if (bounds && boundsPadding === 1 && minZoom === 1) {
            transform.scale *= ratio;
            keepTransformInsideBounds();
        } else {
            var transformAdjusted = keepTransformInsideBounds();
            if (!transformAdjusted) transform.scale *= ratio;
        }

        triggerEvent('zoom');

        makeDirty();
    }

    function zoomAbs(clientX, clientY, zoomLevel) {
        var ratio = zoomLevel / transform.scale;
        zoomByRatio(clientX, clientY, ratio);
    }

    function centerOn(ui) {
        var parent = ui.ownerSVGElement;
        if (!parent)
            throw new Error('ui element is required to be within the scene');

        // TODO: should i use controller's screen CTM?
        var clientRect = ui.getBoundingClientRect();
        var cx = clientRect.left + clientRect.width / 2;
        var cy = clientRect.top + clientRect.height / 2;

        var container = parent.getBoundingClientRect();
        var dx = container.width / 2 - cx;
        var dy = container.height / 2 - cy;

        internalMoveBy(dx, dy, true);
    }

    function internalMoveBy(dx, dy, smooth) {
        if (!smooth) {
            return moveBy(dx, dy);
        }

        if (moveByAnimation) moveByAnimation.cancel();

        var from = {x: 0, y: 0};
        var to = {x: dx, y: dy};
        var lastX = 0;
        var lastY = 0;

        moveByAnimation = animate(from, to, {
            step: function (v) {
                moveBy(v.x - lastX, v.y - lastY);

                lastX = v.x;
                lastY = v.y;
            }
        });
    }

    function scroll(x, y) {
        cancelZoomAnimation();
        moveTo(x, y);
    }

    function dispose() {
        releaseEvents();
    }

    function addWheelListener(element, listener, useCapture) {
        element.addEventListener('wheel', listener, useCapture);
    }

    function removeWheelListener(element, listener, useCapture) {
        element.removeEventListener('wheel', listener, useCapture);
    }

    function listenForEvents() {
        owner.addEventListener('mousedown', onMouseDown, {passive: false});
        owner.addEventListener('dblclick', onDoubleClick, {passive: false});
        owner.addEventListener('touchstart', onTouch, {passive: false});
        owner.addEventListener('keydown', onKeyDown, {passive: false});

        // Need to listen on the owner container, so that we are not limited
        // by the size of the scrollable domElement
        addWheelListener(owner, onMouseWheel, {passive: false});

        makeDirty();
    }

    function releaseEvents() {
        removeWheelListener(owner, onMouseWheel);
        owner.removeEventListener('mousedown', onMouseDown);
        owner.removeEventListener('keydown', onKeyDown);
        owner.removeEventListener('dblclick', onDoubleClick);
        owner.removeEventListener('touchstart', onTouch);

        if (frameAnimation) {
            window.cancelAnimationFrame(frameAnimation);
            frameAnimation = 0;
        }

        smoothScroll.cancel();

        releaseDocumentMouse();
        releaseTouches();

        triggerPanEnd();
    }

    function frame() {
        if (isDirty) applyTransform();
    }

    function applyTransform() {
        isDirty = false;

        // TODO: Should I allow to cancel this?
        panController.applyTransform(transform);

        triggerEvent('transform');
        frameAnimation = 0;
    }

    function onKeyDown(e) {
        var x = 0,
            y = 0,
            z = 0;
        if (e.keyCode === 38) {
            y = 1; // up
        } else if (e.keyCode === 40) {
            y = -1; // down
        } else if (e.keyCode === 37) {
            x = 1; // left
        } else if (e.keyCode === 39) {
            x = -1; // right
        } else if (e.keyCode === 189 || e.keyCode === 109) {
            // DASH or SUBTRACT
            z = 1; // `-` -  zoom out
        } else if (e.keyCode === 187 || e.keyCode === 107) {
            // EQUAL SIGN or ADD
            z = -1; // `=` - zoom in (equal sign on US layout is under `+`)
        }

        if (filterKey(e, x, y, z)) {
            // They don't want us to handle the key: https://github.com/anvaka/panzoom/issues/45
            return;
        }

        if (x || y) {
            e.preventDefault();
            e.stopPropagation();

            var clientRect = owner.getBoundingClientRect();
            // movement speed should be the same in both X and Y direction:
            var offset = Math.min(clientRect.width, clientRect.height);
            var moveSpeedRatio = 0.05;
            var dx = offset * moveSpeedRatio * x;
            var dy = offset * moveSpeedRatio * y;

            // TODO: currently we do not animate this. It could be better to have animation
            internalMoveBy(dx, dy);
        }

        if (z) {
            var scaleMultiplier = getScaleMultiplier(z * 100);
            var offset = transformOrigin ? getTransformOriginOffset() : midPoint();
            publicZoomTo(offset.x, offset.y, scaleMultiplier);
        }
    }

    function midPoint() {
        var ownerRect = owner.getBoundingClientRect();
        return {
            x: ownerRect.width / 2,
            y: ownerRect.height / 2
        };
    }

    function onTouch(e) {
        // let the override the touch behavior
        beforeTouch(e);

        if (e.touches.length === 1) {
            return handleSingleFingerTouch(e, e.touches[0]);
        } else if (e.touches.length === 2) {
            // handleTouchMove() will care about pinch zoom.
            pinchZoomLength = getPinchZoomLength(e.touches[0], e.touches[1]);
            multiTouch = true;
            startTouchListenerIfNeeded();
        }
    }

    function beforeTouch(e) {
        // TODO: Need to unify this filtering names. E.g. use `beforeTouch`
        if (options.onTouch && !options.onTouch(e)) {
            // if they return `false` from onTouch, we don't want to stop
            // events propagation. Fixes https://github.com/anvaka/panzoom/issues/12
            return;
        }

        e.stopPropagation();
        e.preventDefault();
    }

    function beforeDoubleClick(e) {
        // TODO: Need to unify this filtering names. E.g. use `beforeDoubleClick``
        if (options.onDoubleClick && !options.onDoubleClick(e)) {
            // if they return `false` from onTouch, we don't want to stop
            // events propagation. Fixes https://github.com/anvaka/panzoom/issues/46
            return;
        }

        e.preventDefault();
        e.stopPropagation();
    }

    function handleSingleFingerTouch(e) {
        var touch = e.touches[0];
        var offset = getOffsetXY(touch);
        lastSingleFingerOffset = offset;
        var point = transformToScreen(offset.x, offset.y);
        mouseX = point.x;
        mouseY = point.y;

        smoothScroll.cancel();
        startTouchListenerIfNeeded();
    }

    function startTouchListenerIfNeeded() {
        if (touchInProgress) {
            // no need to do anything, as we already listen to events;
            return;
        }

        touchInProgress = true;
        document.addEventListener('touchmove', handleTouchMove);
        document.addEventListener('touchend', handleTouchEnd);
        document.addEventListener('touchcancel', handleTouchEnd);
    }

    function handleTouchMove(e) {
        if (e.touches.length === 1) {
            e.stopPropagation();
            var touch = e.touches[0];

            var offset = getOffsetXY(touch);
            var point = transformToScreen(offset.x, offset.y);

            var dx = point.x - mouseX;
            var dy = point.y - mouseY;

            if (dx !== 0 && dy !== 0) {
                triggerPanStart();
            }
            mouseX = point.x;
            mouseY = point.y;
            internalMoveBy(dx, dy);
        } else if (e.touches.length === 2) {
            // it's a zoom, let's find direction
            multiTouch = true;
            var t1 = e.touches[0];
            var t2 = e.touches[1];
            var currentPinchLength = getPinchZoomLength(t1, t2);

            // since the zoom speed is always based on distance from 1, we need to apply
            // pinch speed only on that distance from 1:
            var scaleMultiplier =
                1 + (currentPinchLength / pinchZoomLength - 1) * pinchSpeed;

            var firstTouchPoint = getOffsetXY(t1);
            var secondTouchPoint = getOffsetXY(t2);
            mouseX = (firstTouchPoint.x + secondTouchPoint.x) / 2;
            mouseY = (firstTouchPoint.y + secondTouchPoint.y) / 2;
            if (transformOrigin) {
                var offset = getTransformOriginOffset();
                mouseX = offset.x;
                mouseY = offset.y;
            }

            publicZoomTo(mouseX, mouseY, scaleMultiplier);

            pinchZoomLength = currentPinchLength;
            e.stopPropagation();
            e.preventDefault();
        }
    }

    function handleTouchEnd(e) {
        if (e.touches.length > 0) {
            var offset = getOffsetXY(e.touches[0]);
            var point = transformToScreen(offset.x, offset.y);
            mouseX = point.x;
            mouseY = point.y;
        } else {
            var now = new Date();
            if (now - lastTouchEndTime < doubleTapSpeedInMS) {
                if (transformOrigin) {
                    var offset = getTransformOriginOffset();
                    smoothZoom(offset.x, offset.y, zoomDoubleClickSpeed);
                } else {
                    // We want untransformed x/y here.
                    smoothZoom(lastSingleFingerOffset.x, lastSingleFingerOffset.y, zoomDoubleClickSpeed);
                }
            }

            lastTouchEndTime = now;

            triggerPanEnd();
            releaseTouches();
        }
    }

    function getPinchZoomLength(finger1, finger2) {
        var dx = finger1.clientX - finger2.clientX;
        var dy = finger1.clientY - finger2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    function onDoubleClick(e) {
        beforeDoubleClick(e);
        var offset = getOffsetXY(e);
        if (transformOrigin) {
            // TODO: looks like this is duplicated in the file.
            // Need to refactor
            offset = getTransformOriginOffset();
        }
        smoothZoom(offset.x, offset.y, zoomDoubleClickSpeed);
    }

    function onMouseDown(e) {
        // if client does not want to handle this event - just ignore the call
        if (beforeMouseDown(e)) return;

        if (touchInProgress) {
            // modern browsers will fire mousedown for touch events too
            // we do not want this: touch is handled separately.
            e.stopPropagation();
            return false;
        }
        // for IE, left click == 1
        // for Firefox, left click == 0
        var isLeftButton =
            (e.button === 1 && window.event !== null) || e.button === 0;
        if (!isLeftButton) return;

        smoothScroll.cancel();

        var offset = getOffsetXY(e);
        var point = transformToScreen(offset.x, offset.y);
        mouseX = point.x;
        mouseY = point.y;

        // We need to listen on document itself, since mouse can go outside of the
        // window, and we will loose it
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);

        return false;
    }

    function onMouseMove(e) {
        // no need to worry about mouse events when touch is happening
        if (touchInProgress) return;

        triggerPanStart();

        var offset = getOffsetXY(e);
        var point = transformToScreen(offset.x, offset.y);
        var dx = point.x - mouseX;
        var dy = point.y - mouseY;

        mouseX = point.x;
        mouseY = point.y;

        internalMoveBy(dx, dy);
    }

    function onMouseUp() {
        triggerPanEnd();
        releaseDocumentMouse();
    }

    function releaseDocumentMouse() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        panstartFired = false;
    }

    function releaseTouches() {
        document.removeEventListener('touchmove', handleTouchMove);
        document.removeEventListener('touchend', handleTouchEnd);
        document.removeEventListener('touchcancel', handleTouchEnd);
        panstartFired = false;
        multiTouch = false;
        touchInProgress = false;
    }

    function onMouseWheel(e) {
        // if client does not want to handle this event - just ignore the call
        if (beforeWheel(e)) return;

        smoothScroll.cancel();

        var delta = e.deltaY;
        if (e.deltaMode > 0) delta *= 100;

        var scaleMultiplier = getScaleMultiplier(delta);

        if (scaleMultiplier !== 1) {
            var offset = transformOrigin
                ? getTransformOriginOffset()
                : getOffsetXY(e);
            publicZoomTo(offset.x, offset.y, scaleMultiplier);
            e.preventDefault();
        }
    }

    function getOffsetXY(e) {
        var offsetX, offsetY;
        // I tried using e.offsetX, but that gives wrong results for svg, when user clicks on a path.
        var ownerRect = owner.getBoundingClientRect();
        offsetX = e.clientX - ownerRect.left;
        offsetY = e.clientY - ownerRect.top;

        return {x: offsetX, y: offsetY};
    }

    function smoothZoom(clientX, clientY, scaleMultiplier) {
        var fromValue = transform.scale;
        var from = {scale: fromValue};
        var to = {scale: scaleMultiplier * fromValue};

        smoothScroll.cancel();
        cancelZoomAnimation();

        zoomToAnimation = animate(from, to, {
            step: function (v) {
                zoomAbs(clientX, clientY, v.scale);
            },
            done: triggerZoomEnd
        });
    }

    function smoothZoomAbs(clientX, clientY, toScaleValue) {
        var fromValue = transform.scale;
        var from = {scale: fromValue};
        var to = {scale: toScaleValue};

        smoothScroll.cancel();
        cancelZoomAnimation();

        zoomToAnimation = animate(from, to, {
            step: function (v) {
                zoomAbs(clientX, clientY, v.scale);
            }
        });
    }

    function getTransformOriginOffset() {
        var ownerRect = owner.getBoundingClientRect();
        return {
            x: ownerRect.width * transformOrigin.x,
            y: ownerRect.height * transformOrigin.y
        };
    }

    function publicZoomTo(clientX, clientY, scaleMultiplier) {
        smoothScroll.cancel();
        // cancelZoomAnimation();
        return zoomByRatio(clientX, clientY, scaleMultiplier);
    }

    function cancelZoomAnimation() {
        if (zoomToAnimation) {
            zoomToAnimation.cancel();
            zoomToAnimation = null;
        }
    }

    function getScaleMultiplier(delta) {
        var sign = Math.sign(delta);
        var deltaAdjustedSpeed = Math.min(0.25, Math.abs(speed * delta / 128));
        return 1 - sign * deltaAdjustedSpeed;
    }

    function triggerPanStart() {
        if (!panstartFired) {
            triggerEvent('panstart');
            panstartFired = true;
            smoothScroll.start();
        }
    }

    function triggerPanEnd() {
        if (panstartFired) {
            // we should never run smooth scrolling if it was multiTouch (pinch zoom animation):
            if (!multiTouch) smoothScroll.stop();
            triggerEvent('panend');
        }
    }

    function triggerZoomEnd() {
        triggerEvent('zoomend');
    }

    function triggerEvent(name) {
        api.fire(name, api);
    }
}

function parseTransformOrigin(options) {
    if (!options) return;
    if (typeof options === 'object') {
        if (!isNumber(options.x) || !isNumber(options.y))
            failTransformOrigin(options);
        return options;
    }

    failTransformOrigin();
}

function failTransformOrigin(options) {
    console.error(options);
    throw new Error(
        [
            'Cannot parse transform origin.',
            'Some good examples:',
            '  "center center" can be achieved with {x: 0.5, y: 0.5}',
            '  "top center" can be achieved with {x: 0.5, y: 0}',
            '  "bottom right" can be achieved with {x: 1, y: 1}'
        ].join('\n')
    );
}

function noop() {
}

function validateBounds(bounds) {
    var boundsType = typeof bounds;
    if (boundsType === 'undefined' || boundsType === 'boolean') return; // this is okay
    // otherwise need to be more thorough:
    var validBounds =
        isNumber(bounds.left) &&
        isNumber(bounds.top) &&
        isNumber(bounds.bottom) &&
        isNumber(bounds.right);

    if (!validBounds)
        throw new Error(
            'Bounds object is not valid. It can be: ' +
            'undefined, boolean (true|false) or an object {left, top, right, bottom}'
        );
}

function isNumber(x) {
    return Number.isFinite(x);
}

// IE 11 does not support isNaN:
function isNaN(value) {
    if (Number.isNaN) {
        return Number.isNaN(value);
    }

    return value !== value;
}

function rigidScroll() {
    return {
        start: noop,
        stop: noop,
        cancel: noop
    };
}

function autoRun() {
    if (typeof document === 'undefined') return;

    var scripts = document.getElementsByTagName('script');
    if (!scripts) return;
    var panzoomScript;

    for (var i = 0; i < scripts.length; ++i) {
        var x = scripts[i];
        if (x.src && x.src.match(/\bpanzoom(\.min)?\.js/)) {
            panzoomScript = x;
            break;
        }
    }

    if (!panzoomScript) return;

    var query = panzoomScript.getAttribute('query');
    if (!query) return;

    var globalName = panzoomScript.getAttribute('name') || 'pz';
    var started = Date.now();

    tryAttach();

    function tryAttach() {
        var el = document.querySelector(query);
        if (!el) {
            var now = Date.now();
            var elapsed = now - started;
            if (elapsed < 2000) {
                // Let's wait a bit
                setTimeout(tryAttach, 100);
                return;
            }
            // If we don't attach within 2 seconds to the target element, consider it a failure
            console.error('Cannot find the panzoom element', globalName);
            return;
        }
        var options = collectOptions(panzoomScript);
        console.log(options);
        window[globalName] = createPanZoom(el, options);
    }

    function collectOptions(script) {
        var attrs = script.attributes;
        var options = {};
        for (var i = 0; i < attrs.length; ++i) {
            var attr = attrs[i];
            var nameValue = getPanzoomAttributeNameValue(attr);
            if (nameValue) {
                options[nameValue.name] = nameValue.value;
            }
        }

        return options;
    }

    function getPanzoomAttributeNameValue(attr) {
        if (!attr.name) return;
        var isPanZoomAttribute =
            attr.name[0] === 'p' && attr.name[1] === 'z' && attr.name[2] === '-';

        if (!isPanZoomAttribute) return;

        var name = attr.name.substr(3);
        var value = JSON.parse(attr.value);
        return {name: name, value: value};
    }
}

autoRun();

function eventify(subject) {
    validateSubject(subject);

    var eventsStorage = createEventsStorage(subject);
    subject.on = eventsStorage.on;
    subject.off = eventsStorage.off;
    subject.fire = eventsStorage.fire;
    return subject;
}

function createEventsStorage(subject) {
    // Store all event listeners to this hash. Key is event name, value is array
    // of callback records.
    //
    // A callback record consists of callback function and its optional context:
    // { 'eventName' => [{callback: function, ctx: object}] }
    var registeredEvents = Object.create(null);

    return {
        on: function (eventName, callback, ctx) {
            if (typeof callback !== 'function') {
                throw new Error('callback is expected to be a function');
            }
            var handlers = registeredEvents[eventName];
            if (!handlers) {
                handlers = registeredEvents[eventName] = [];
            }
            handlers.push({callback: callback, ctx: ctx});

            return subject;
        },

        off: function (eventName, callback) {
            var wantToRemoveAll = (typeof eventName === 'undefined');
            if (wantToRemoveAll) {
                // Killing old events storage should be enough in this case:
                registeredEvents = Object.create(null);
                return subject;
            }

            if (registeredEvents[eventName]) {
                var deleteAllCallbacksForEvent = (typeof callback !== 'function');
                if (deleteAllCallbacksForEvent) {
                    delete registeredEvents[eventName];
                } else {
                    var callbacks = registeredEvents[eventName];
                    for (var i = 0; i < callbacks.length; ++i) {
                        if (callbacks[i].callback === callback) {
                            callbacks.splice(i, 1);
                        }
                    }
                }
            }

            return subject;
        },

        fire: function (eventName) {
            var callbacks = registeredEvents[eventName];
            if (!callbacks) {
                return subject;
            }

            var fireArguments;
            if (arguments.length > 1) {
                fireArguments = Array.prototype.splice.call(arguments, 1);
            }
            for (var i = 0; i < callbacks.length; ++i) {
                var callbackInfo = callbacks[i];
                callbackInfo.callback.apply(callbackInfo.ctx, fireArguments);
            }

            return subject;
        }
    };
}

function validateSubject(subject) {
    if (!subject) {
        throw new Error('Eventify cannot use falsy object as events subject');
    }
    var reservedWords = ['on', 'fire', 'off'];
    for (var i = 0; i < reservedWords.length; ++i) {
        if (subject.hasOwnProperty(reservedWords[i])) {
            throw new Error("Subject cannot be eventified, since it already has property '" + reservedWords[i] + "'");
        }
    }
}


