/**
 * Three.js renderer initialization and core rendering loop.
 */

export class Renderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.animationId = null;
        
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0a);
        
        // Create camera
        const aspect = window.innerWidth / window.innerHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(15, 15, 15);
        this.camera.lookAt(0, 0, 0);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: false
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight1.position.set(10, 10, 10);
        this.scene.add(directionalLight1);
        
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.2);
        directionalLight2.position.set(-10, -10, -10);
        this.scene.add(directionalLight2);
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }

    onWindowResize() {
        const aspect = window.innerWidth / window.innerHeight;
        this.camera.aspect = aspect;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    render() {
        this.renderer.render(this.scene, this.camera);
    }

    startAnimationLoop(callback) {
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);
            
            if (callback) {
                callback();
            }
            
            this.render();
        };
        
        animate();
    }

    stopAnimationLoop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }

    getScene() {
        return this.scene;
    }

    getCamera() {
        return this.camera;
    }

    getRenderer() {
        return this.renderer;
    }
}
