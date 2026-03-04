/**
 * Camera controls and user input handling.
 */

export class InputController {
    constructor(camera, canvas) {
        this.camera = camera;
        this.canvas = canvas;
        
        // Camera control state
        this.rotationSpeed = 0.02;
        this.panSpeed = 0.5;
        this.zoomSpeed = 1.0;
        
        // Mouse state
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        
        // Raycaster for node selection
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Callbacks
        this.onNodeClick = null;
        this.onNodeHover = null;
        
        this.initEventListeners();
    }

    initEventListeners() {
        // Keyboard controls
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
        
        // Mouse controls
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('click', (e) => this.onClick(e));
        
        // Wheel for zoom
        this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });
    }

    onKeyDown(event) {
        const rotSpeed = this.rotationSpeed;
        
        switch(event.key) {
            case 'ArrowUp':
                this.camera.position.y += rotSpeed * 10;
                event.preventDefault();
                break;
            case 'ArrowDown':
                this.camera.position.y -= rotSpeed * 10;
                event.preventDefault();
                break;
            case 'ArrowLeft':
                // Rotate camera around Y axis
                this.rotateAroundCenter(-rotSpeed * 3);
                event.preventDefault();
                break;
            case 'ArrowRight':
                // Rotate camera around Y axis
                this.rotateAroundCenter(rotSpeed * 3);
                event.preventDefault();
                break;
        }
        
        this.camera.lookAt(0, 0, 0);
    }

    rotateAroundCenter(angle) {
        const x = this.camera.position.x;
        const z = this.camera.position.z;
        
        this.camera.position.x = x * Math.cos(angle) - z * Math.sin(angle);
        this.camera.position.z = x * Math.sin(angle) + z * Math.cos(angle);
    }

    onMouseDown(event) {
        this.isDragging = true;
        this.previousMousePosition = {
            x: event.clientX,
            y: event.clientY
        };
    }

    onMouseMove(event) {
        if (this.isDragging) {
            const deltaX = event.clientX - this.previousMousePosition.x;
            const deltaY = event.clientY - this.previousMousePosition.y;
            
            // Pan camera
            const panX = -deltaX * this.panSpeed * 0.02;
            const panY = deltaY * this.panSpeed * 0.02;
            
            this.camera.position.x += panX;
            this.camera.position.y += panY;
            
            this.previousMousePosition = {
                x: event.clientX,
                y: event.clientY
            };
        } else {
            // Update raycaster for hover detection
            this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        }
    }

    onMouseUp(event) {
        this.isDragging = false;
    }

    onClick(event) {
        // Raycast to detect node clicks
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        
        const intersectedNode = this.getIntersectedNode();
        
        if (intersectedNode && this.onNodeClick) {
            this.onNodeClick(intersectedNode);
        }
    }

    onWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY;
        const zoomFactor = 1 + (delta > 0 ? -0.1 : 0.1);
        
        // Zoom by moving camera closer/further
        this.camera.position.multiplyScalar(zoomFactor);
        
        // Constrain zoom limits
        const distance = this.camera.position.length();
        if (distance < 5) {
            this.camera.position.normalize().multiplyScalar(5);
        } else if (distance > 200) {
            this.camera.position.normalize().multiplyScalar(200);
        }
    }

    /**
     * Get the node that the cursor is currently over.
     */
    getIntersectedNode() {
        if (!this.nodeMeshes || this.nodeMeshes.length === 0) {
            return null;
        }
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.nodeMeshes);
        
        if (intersects.length > 0) {
            return intersects[0].object.userData;
        }
        
        return null;
    }

    /**
     * Set the node meshes for raycasting.
     */
    setNodeMeshes(meshes) {
        this.nodeMeshes = meshes;
    }

    /**
     * Register callback for node click events.
     */
    setNodeClickCallback(callback) {
        this.onNodeClick = callback;
    }

    /**
     * Register callback for node hover events.
     */
    setNodeHoverCallback(callback) {
        this.onNodeHover = callback;
    }
}
