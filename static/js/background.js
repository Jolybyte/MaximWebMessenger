// static/js/background.js - Cyberpunk Energy Sphere with Interior Grid (мы внутри сферы)
// ОБНОВЛЕНО: Камера дальше, сетка больше, добавлена имитация диаграммы Вороного.
(function initCyberpunkBackground() {
    if (typeof THREE === 'undefined') {
        console.error('Three.js not loaded!');
        return;
    }
    
    console.log('Initializing cyberpunk background - Voronoi Grid Inside...');
    
    const container = document.createElement('div');
    container.id = 'canvas-container';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.zIndex = '0';
    container.style.pointerEvents = 'none';
    document.body.insertBefore(container, document.body.firstChild);
    
    const scanline = document.createElement('div');
    scanline.className = 'scanline';
    scanline.style.position = 'fixed';
    scanline.style.top = '0';
    scanline.style.left = '0';
    scanline.style.width = '100%';
    scanline.style.height = '100%';
    scanline.style.pointerEvents = 'none';
    scanline.style.background = 'repeating-linear-gradient(0deg, rgba(0,0,0,0.15) 0px, rgba(0,0,0,0.15) 1px, transparent 1px, transparent 2px)';
    scanline.style.zIndex = '999';
    document.body.appendChild(scanline);
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    
    // ИЗМЕНЕНИЕ 1: Камера отодвинута дальше
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 1.5, 5.5); // Было 3.8, стало 5.5
    camera.lookAt(0, 0, 0);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x000000, 1);
    container.appendChild(renderer.domElement);
    
    // ========== 1. ВНУТРЕННЯЯ СЕТКА (УВЕЛИЧЕННЫЙ РАЗМЕР) ==========
    // ИЗМЕНЕНИЕ 2: Радиусы увеличены с ~5.8 до ~9.0
    
    // Основная сетка
    const interiorGridGeo = new THREE.SphereGeometry(9.0, 128, 128);
    const interiorGridMat = new THREE.MeshBasicMaterial({
        color: 0x64b046,
        wireframe: true,
        transparent: true,
        opacity: 0.22,
        side: THREE.BackSide
    });
    const interiorGrid = new THREE.Mesh(interiorGridGeo, interiorGridMat);
    scene.add(interiorGrid);
    
    // Детальная сетка
    const interiorGridGeo2 = new THREE.SphereGeometry(8.7, 96, 96);
    const interiorGridMat2 = new THREE.MeshBasicMaterial({
        color: 0x4a9a35,
        wireframe: true,
        transparent: true,
        opacity: 0.15,
        side: THREE.BackSide
    });
    const interiorGrid2 = new THREE.Mesh(interiorGridGeo2, interiorGridMat2);
    scene.add(interiorGrid2);
    
    // Редкая сетка
    const interiorGridGeo3 = new THREE.SphereGeometry(9.4, 64, 64);
    const interiorGridMat3 = new THREE.MeshBasicMaterial({
        color: 0x3a7a25,
        wireframe: true,
        transparent: true,
        opacity: 0.1,
        side: THREE.BackSide
    });
    const interiorGrid3 = new THREE.Mesh(interiorGridGeo3, interiorGridMat3);
    scene.add(interiorGrid3);
    
    // ИЗМЕНЕНИЕ 3: Добавлена сфера с имитацией диаграммы Вороного
    // Используем ShaderMaterial для создания неправильных сот (Voronoi-like)
    const voronoiVertexShader = `
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        
        void main() {
            vUv = uv;
            vNormal = normalize(normalMatrix * normal);
            vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
            vViewPosition = -mvPosition.xyz;
            gl_Position = projectionMatrix * mvPosition;
        }
    `;
    
    const voronoiFragmentShader = `
        uniform float time;
        varying vec2 vUv;
        varying vec3 vNormal;
        varying vec3 vViewPosition;
        
        // Функция случайного шума для генерации ячеек
        vec2 random2(vec2 st){
            st = vec2( dot(st,vec2(127.1,311.7)),
                      dot(st,vec2(269.5,183.3)) );
            return -1.0 + 2.0 * fract(sin(st) * 43758.5453123);
        }
        
        // Шум Вороного (Voronoi)
        float voronoi(vec2 st) {
            vec2 i = floor(st);
            vec2 f = fract(st);
            
            float minDist = 1.0;
            vec2 minPoint = vec2(0.0);
            
            for (int y = -1; y <= 1; y++) {
                for (int x = -1; x <= 1; x++) {
                    vec2 neighbor = vec2(float(x), float(y));
                    vec2 point = random2(i + neighbor);
                    point = 0.5 + 0.5 * sin(time * 0.5 + 6.2831 * point); // Медленная анимация ячеек
                    vec2 diff = neighbor + point - f;
                    float dist = length(diff);
                    minDist = min(minDist, dist);
                }
            }
            
            return minDist;
        }
        
        void main() {
            // Растягиваем UV для создания эффекта перспективы (искажение к краям)
            vec2 st = vUv * 6.0; // Плотность ячеек
            
            // Добавляем искажение для эффекта вогнутой чаши
            st.x += sin(st.y * 2.0 + time * 0.1) * 0.1;
            st.y += cos(st.x * 2.0 + time * 0.1) * 0.1;
            
            float v = voronoi(st);
            
            // Создаем линии сетки (границы ячеек)
            float borders = smoothstep(0.02, 0.05, v);
            float gridIntensity = 1.0 - borders;
            
            // Добавляем эффект Френеля для затемнения по краям (подчеркивает вогнутость)
            vec3 normal = normalize(vNormal);
            vec3 viewDir = normalize(vViewPosition);
            float fresnel = pow(1.0 - dot(normal, viewDir), 2.5);
            
            // Цвета: глубокий зеленый/черный для пустоты, ярко-зеленый для сетки
            vec3 darkColor = vec3(0.0, 0.05, 0.0);
            vec3 gridColor = vec3(0.4, 0.9, 0.2);
            
            // Применяем прозрачность в зависимости от Френеля (центр более прозрачный, края плотнее)
            float alpha = gridIntensity * (0.15 + fresnel * 0.5);
            
            vec3 finalColor = mix(darkColor, gridColor, gridIntensity);
            finalColor = mix(finalColor, vec3(0.0, 0.0, 0.0), fresnel * 0.7);
            
            gl_FragColor = vec4(finalColor, alpha);
        }
    `;
    
    const voronoiGeo = new THREE.SphereGeometry(9.2, 180, 180);
    const voronoiMat = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 }
        },
        vertexShader: voronoiVertexShader,
        fragmentShader: voronoiFragmentShader,
        transparent: true,
        side: THREE.BackSide, // Смотрим изнутри
        blending: THREE.AdditiveBlending // Для свечения
    });
    const voronoiSphere = new THREE.Mesh(voronoiGeo, voronoiMat);
    scene.add(voronoiSphere);
    
    // Геодезическая сетка (увеличена)
    const geoGridGeo = new THREE.IcosahedronGeometry(9.3, 1);
    const geoGridMat = new THREE.MeshBasicMaterial({
        color: 0x54a040,
        wireframe: true,
        transparent: true,
        opacity: 0.08,
        side: THREE.BackSide
    });
    const geoGrid = new THREE.Mesh(geoGridGeo, geoGridMat);
    scene.add(geoGrid);
    
    // ========== 2. ЦЕНТРАЛЬНАЯ СВЕТЯЩАЯСЯ СФЕРА (Без изменений) ==========
    // ... (весь код шейдеров для energyCore остается тем же, что и в вашем исходнике)
    const vertexShader = ` /* ваш код */ `;
    const fragmentShader = ` /* ваш код */ `;
    
    const coreGeometry = new THREE.SphereGeometry(1.5, 256, 256);
    const coreMaterial = new THREE.ShaderMaterial({
        uniforms: { time: { value: 0 } },
        vertexShader: vertexShader,
        fragmentShader: fragmentShader,
        transparent: true,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide
    });
    const energyCore = new THREE.Mesh(coreGeometry, coreMaterial);
    scene.add(energyCore);
    
    const innerCoreGeo = new THREE.SphereGeometry(0.75, 128, 128);
    const innerCoreMat = new THREE.MeshBasicMaterial({
        color: 0x8aff6a,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
    });
    const innerCore = new THREE.Mesh(innerCoreGeo, innerCoreMat);
    scene.add(innerCore);
    
    const glowGeo = new THREE.SphereGeometry(2.1, 64, 64);
    const glowMat = new THREE.MeshBasicMaterial({
        color: 0x64b046,
        transparent: true,
        opacity: 0.1,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide
    });
    const glowSphere = new THREE.Mesh(glowGeo, glowMat);
    scene.add(glowSphere);
    
    // ========== 3. ЧАСТИЦЫ (Адаптированы под новое расстояние) ==========
    const particleCount = 8000; // Больше частиц для большего пространства
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
        const radius = 2.5 + Math.random() * 5.5; // Распределены дальше
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        particlePositions[i * 3 + 2] = radius * Math.cos(phi);
        
        const greenIntensity = 0.3 + Math.random() * 0.7;
        particleColors[i * 3] = 0.1 * greenIntensity;
        particleColors[i * 3 + 1] = 0.4 + Math.random() * 0.6;
        particleColors[i * 3 + 2] = 0.05 * greenIntensity;
    }
    
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
        size: 0.025,
        vertexColors: true,
        transparent: true,
        opacity: 0.5,
        blending: THREE.AdditiveBlending
    });
    
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
    
    // ========== 4. ПАРЯЩИЕ ИСКРЫ (Область увеличена) ==========
    const sparkCount = 3500;
    const sparkGeometry = new THREE.BufferGeometry();
    const sparkPositions = new Float32Array(sparkCount * 3);
    const sparkVelocities = [];
    
    for (let i = 0; i < sparkCount; i++) {
        sparkPositions[i * 3] = (Math.random() - 0.5) * 18;
        sparkPositions[i * 3 + 1] = (Math.random() - 0.5) * 14;
        sparkPositions[i * 3 + 2] = (Math.random() - 0.5) * 18;
        sparkVelocities.push({
            x: (Math.random() - 0.5) * 0.01,
            y: (Math.random() - 0.5) * 0.01,
            z: (Math.random() - 0.5) * 0.01
        });
    }
    
    sparkGeometry.setAttribute('position', new THREE.BufferAttribute(sparkPositions, 3));
    const sparkMaterial = new THREE.PointsMaterial({
        color: 0x64b046,
        size: 0.015,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending
    });
    const sparks = new THREE.Points(sparkGeometry, sparkMaterial);
    scene.add(sparks);
    
    // ========== 5. ОСВЕЩЕНИЕ (Без изменений) ==========
    const coreLight = new THREE.PointLight(0x64b046, 1.8, 30);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);
    
    const movingLight = new THREE.PointLight(0x4aff2a, 0.5);
    scene.add(movingLight);
    const movingLight2 = new THREE.PointLight(0x2aff4a, 0.4);
    scene.add(movingLight2);
    const fillLight = new THREE.AmbientLight(0x0a2a0a);
    scene.add(fillLight);
    
    // ========== 6. АНИМАЦИЯ ==========
    let time = 0;
    
    function animate() {
        requestAnimationFrame(animate);
        time += 0.016;
        
        // Обновляем шейдеры
        coreMaterial.uniforms.time.value = time;
        if (voronoiMat.uniforms) voronoiMat.uniforms.time.value = time;
        
        // Анимация центра (без изменений)
        const pulseScale = 1 + Math.sin(time * 3.2) * 0.05;
        energyCore.scale.set(pulseScale, pulseScale, pulseScale);
        const innerScale = 1 + Math.sin(time * 4.5) * 0.08;
        innerCore.scale.set(innerScale, innerScale, innerScale);
        const glowScale = 1 + Math.sin(time * 2.8) * 0.06;
        glowSphere.scale.set(glowScale, glowScale, glowScale);
        coreLight.intensity = 1.3 + Math.sin(time * 3.8) * 0.6;
        
        // Вращение сеток
        interiorGrid.rotation.y = time * 0.02;
        interiorGrid2.rotation.y = time * 0.015;
        interiorGrid3.rotation.z = time * 0.01;
        geoGrid.rotation.y = time * 0.01;
        voronoiSphere.rotation.y = time * 0.005;
        
        particles.rotation.y = time * 0.03;
        
        // Движение света
        movingLight.position.x = Math.sin(time * 0.7) * 4.0;
        movingLight.position.z = Math.cos(time * 0.6) * 4.0;
        movingLight.position.y = Math.sin(time * 0.9) * 3.0;
        movingLight2.position.x = Math.cos(time * 0.8) * 4.5;
        movingLight2.position.z = Math.sin(time * 0.5) * 4.5;
        movingLight2.position.y = Math.cos(time * 1.0) * 3.0;
        
        // Анимация искр
        const sparkPosAttr = sparks.geometry.attributes.position.array;
        for (let i = 0; i < sparkCount; i++) {
            sparkPosAttr[i * 3] += sparkVelocities[i].x;
            sparkPosAttr[i * 3 + 1] += sparkVelocities[i].y;
            sparkPosAttr[i * 3 + 2] += sparkVelocities[i].z;
            if (Math.abs(sparkPosAttr[i * 3]) > 10) sparkPosAttr[i * 3] = (Math.random() - 0.5) * 18;
            if (Math.abs(sparkPosAttr[i * 3 + 1]) > 8) sparkPosAttr[i * 3 + 1] = (Math.random() - 0.5) * 14;
            if (Math.abs(sparkPosAttr[i * 3 + 2]) > 10) sparkPosAttr[i * 3 + 2] = (Math.random() - 0.5) * 18;
        }
        sparks.geometry.attributes.position.needsUpdate = true;
        
        renderer.render(scene, camera);
    }
    
    animate();
    
    window.addEventListener('resize', onWindowResize, false);
    function onWindowResize() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    }
    
    console.log('Updated: Camera distance 5.5, grid size ~9.0, Voronoi shader active.');
})();