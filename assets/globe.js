import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';

const shell = document.querySelector('[data-tcso-globe]');
const mount = shell?.querySelector('[data-globe-canvas]');
const toggle = shell?.querySelector('.globe-toggle');

if (shell && mount) {
    try {
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
        camera.position.set(0, 0, 5.85);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'low-power' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.15;
        renderer.setClearColor(0x07131d, 0);
        renderer.domElement.setAttribute('aria-label', 'Interactive globe. Drag to rotate; use the arrow keys when focused.');
        renderer.domElement.setAttribute('tabindex', '0');
        renderer.domElement.className = 'globe-canvas-surface';
        mount.append(renderer.domElement);

        const ambient = new THREE.HemisphereLight(0xb7d5d7, 0x07131d, 1.35);
        scene.add(ambient);
        const warmKey = new THREE.DirectionalLight(0xf3d79a, 2.55);
        warmKey.position.set(-3.2, 2.4, 4.5);
        scene.add(warmKey);
        const coolFill = new THREE.DirectionalLight(0x4c8994, 1.2);
        coolFill.position.set(3.5, -1.5, -3.5);
        scene.add(coolFill);

        const earthGroup = new THREE.Group();
        scene.add(earthGroup);
        const radius = 1.68;
        const earthGeometry = new THREE.SphereGeometry(radius, 112, 72);
        const texture = new THREE.TextureLoader().load('/assets/earth-blue-marble.jpg', () => {
            shell.classList.add('is-ready');
        }, undefined, () => {
            shell.classList.add('is-ready');
            shell.classList.add('texture-fallback');
        });
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
        const earth = new THREE.Mesh(earthGeometry, new THREE.MeshPhongMaterial({
            map: texture,
            color: 0xe9e1ce,
            specular: 0x56717a,
            shininess: 11
        }));
        earthGroup.add(earth);

        const atmosphere = new THREE.Mesh(
            new THREE.SphereGeometry(radius * 1.035, 96, 64),
            new THREE.MeshBasicMaterial({ color: 0x4aa6ad, side: THREE.BackSide, transparent: true, opacity: 0.22 })
        );
        earthGroup.add(atmosphere);

        const latLonToVector = (latitude, longitude, distance = radius) => {
            const phi = THREE.MathUtils.degToRad(longitude + 180);
            const theta = THREE.MathUtils.degToRad(90 - latitude);
            return new THREE.Vector3(
                -distance * Math.cos(phi) * Math.sin(theta),
                distance * Math.cos(theta),
                distance * Math.sin(phi) * Math.sin(theta)
            );
        };

        const home = latLonToVector(21.9, 95.9, radius * 1.009);
        // Start with Myanmar facing the viewer so the globe immediately reads as the TCSO diaspora map.
        earthGroup.quaternion.setFromUnitVectors(home.clone().normalize(), new THREE.Vector3(0, 0, 1));
        const pin = new THREE.Mesh(
            new THREE.SphereGeometry(0.033, 18, 14),
            new THREE.MeshBasicMaterial({ color: 0xffd784 })
        );
        pin.position.copy(home);
        earthGroup.add(pin);

        const pinRing = new THREE.Mesh(
            new THREE.RingGeometry(0.047, 0.06, 48),
            new THREE.MeshBasicMaterial({ color: 0xe5c071, transparent: true, opacity: 0.9, side: THREE.DoubleSide })
        );
        pinRing.position.copy(home.clone().normalize().multiplyScalar(radius * 1.014));
        pinRing.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), home.clone().normalize());
        earthGroup.add(pinRing);

        // These are illustrative regional endpoints only; they do not encode member positions or live data.
        const regionalRoutes = [
            [12, 112], [38, 136], [27, 75], [49, 12], [39, -98], [-25, 133]
        ];
        const routeMaterial = new THREE.MeshBasicMaterial({ color: 0xd6b568, transparent: true, opacity: 0.46 });
        const routeHaloMaterial = new THREE.MeshBasicMaterial({ color: 0x86b8bb, transparent: true, opacity: 0.16 });
        regionalRoutes.forEach(([latitude, longitude]) => {
            const start = latLonToVector(21.9, 95.9, radius * 1.012);
            const end = latLonToVector(latitude, longitude, radius * 1.012);
            const midpoint = start.clone().add(end).normalize().multiplyScalar(radius * 1.18);
            const curve = new THREE.QuadraticBezierCurve3(start, midpoint, end);
            const points = curve.getPoints(56);
            const halo = new THREE.Mesh(new THREE.TubeGeometry(curve, 56, 0.0075, 5, false), routeHaloMaterial);
            const core = new THREE.Mesh(new THREE.TubeGeometry(curve, 56, 0.0028, 5, false), routeMaterial);
            earthGroup.add(halo, core);
            const endpoint = new THREE.Mesh(
                new THREE.SphereGeometry(0.012, 12, 10),
                new THREE.MeshBasicMaterial({ color: 0x93c9c5, transparent: true, opacity: 0.78 })
            );
            endpoint.position.copy(points[points.length - 1]);
            earthGroup.add(endpoint);
        });

        const starPositions = [];
        let seed = 4917;
        const random = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
        for (let i = 0; i < 260; i += 1) {
            const u = random() * 2 - 1;
            const angle = random() * Math.PI * 2;
            const spread = 7 + random() * 8;
            const root = Math.sqrt(1 - u * u);
            starPositions.push(spread * root * Math.cos(angle), spread * u, spread * root * Math.sin(angle));
        }
        const starGeometry = new THREE.BufferGeometry();
        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
        const stars = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0x88aeb3, size: 0.018, transparent: true, opacity: 0.5, sizeAttenuation: true }));
        scene.add(stars);

        const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.055;
        controls.enablePan = false;
        controls.minDistance = 3.85;
        controls.maxDistance = 7.1;
        controls.minPolarAngle = 0.58;
        controls.maxPolarAngle = 2.56;
        controls.autoRotate = !reducedMotion.matches;
        controls.autoRotateSpeed = 0.42;
        toggle.hidden = false;
        toggle.textContent = controls.autoRotate ? 'Pause rotation' : 'Start slow rotation';
        toggle.setAttribute('aria-pressed', String(!controls.autoRotate));
        toggle.addEventListener('click', () => {
            controls.autoRotate = !controls.autoRotate;
            toggle.textContent = controls.autoRotate ? 'Pause rotation' : 'Start slow rotation';
            toggle.setAttribute('aria-pressed', String(!controls.autoRotate));
        });

        renderer.domElement.addEventListener('keydown', (event) => {
            const step = event.shiftKey ? 0.24 : 0.12;
            if (event.key === 'ArrowLeft') controls.rotateLeft(step);
            else if (event.key === 'ArrowRight') controls.rotateLeft(-step);
            else if (event.key === 'ArrowUp') controls.rotateUp(step);
            else if (event.key === 'ArrowDown') controls.rotateUp(-step);
            else return;
            event.preventDefault();
            controls.update();
            renderer.render(scene, camera);
        });

        const resize = () => {
            const { width, height } = mount.getBoundingClientRect();
            if (!width || !height) return;
            renderer.setSize(width, height, false);
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
        };
        const resizeObserver = new ResizeObserver(resize);
        resizeObserver.observe(mount);
        resize();

        let inView = true;
        const visibilityObserver = new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; });
        visibilityObserver.observe(shell);
        const clock = new THREE.Clock();
        let lastFrame = 0;
        const animate = (now) => {
            window.requestAnimationFrame(animate);
            if (!inView || document.hidden || now - lastFrame < 32) return;
            controls.update(clock.getDelta());
            renderer.render(scene, camera);
            lastFrame = now;
        };
        window.requestAnimationFrame(animate);

        reducedMotion.addEventListener?.('change', (event) => {
            if (event.matches) {
                controls.autoRotate = false;
                toggle.textContent = 'Start slow rotation';
                toggle.setAttribute('aria-pressed', 'true');
            }
        });
    } catch (error) {
        shell.classList.add('globe-unavailable');
        console.error('TCSO globe could not start.', error);
    }
}
