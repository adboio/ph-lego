(() => {
  const get = id => document.getElementById(id);
  const host = get('model-viewer');
  const scope = get('model-scope');
  const status = get('viewer-status');
  let currentStep = 0;
  let renderer;
  function illustrationOnly(message) {
    host.hidden = true;
    get('assembly').hidden = false;
    get('viewer-help').hidden = true;
    for (const id of ['view-3d', 'model-scope', 'model-reset']) get(id).disabled = true;
    get('view-3d').setAttribute('aria-pressed', 'false');
    get('view-image').setAttribute('aria-pressed', 'true');
    status.textContent = message;
  }
  try {
    renderer = new THREE.WebGLRenderer({antialias: true, alpha: false});
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setClearColor(0xffffff);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, .1, 2000);
    camera.up.set(0, 0, 1);
    const canvas = renderer.domElement;
    canvas.tabIndex = 0;
    canvas.setAttribute('aria-label', 'Interactive Max brick model');
    host.replaceChildren(canvas);
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.listenToKeyEvents(canvas);
    controls.minDistance = 2;
    controls.maxDistance = 160;
    const draw = () => { if (!host.hidden) renderer.render(scene, camera); };
    controls.addEventListener('change', draw);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x768294, 2.2));
    for (const [position, intensity] of [[[20, -30, 40], 2], [[-20, 20, 15], 1]]) {
      const light = new THREE.DirectionalLight(0xffffff, intensity);
      light.position.set(...position);
      scene.add(light);
    }
    const asset = JSON.parse(get('model-geometry').textContent);
    const decode = (value, Type) => {
      const bytes = Uint8Array.from(atob(value), char => char.charCodeAt(0));
      return new Type(bytes.buffer);
    };
    const geometry = new Map();
    for (const [id, source] of Object.entries(asset.geometries)) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(decode(source.positions, Float32Array), 3));
      g.setIndex(new THREE.BufferAttribute(decode(source.indices, Uint32Array), 1));
      g.computeVertexNormals();
      g.computeBoundingBox();
      geometry.set(id, g);
    }
    const groups = new Map();
    const material = new THREE.MeshStandardMaterial({roughness: .72, metalness: 0, side: THREE.DoubleSide});
    for (const item of asset.instances) {
      item.transform = new THREE.Matrix4().set(...item.matrix);
      item.bounds = geometry.get(item.part).boundingBox.clone().applyMatrix4(item.transform);
      if (!groups.has(item.part)) groups.set(item.part, {items: []});
      groups.get(item.part).items.push(item);
    }
    for (const [id, group] of groups) {
      group.mesh = new THREE.InstancedMesh(geometry.get(id), material, group.items.length);
      group.mesh.frustumCulled = false;
      scene.add(group.mesh);
    }
    let bounds = new THREE.Box3();
    const color = new THREE.Color();
    function reset() {
      if (bounds.isEmpty()) return;
      const center = bounds.getCenter(new THREE.Vector3());
      const radius = bounds.getBoundingSphere(new THREE.Sphere()).radius;
      const vertical = THREE.MathUtils.degToRad(camera.fov) / 2;
      const horizontal = Math.atan(Math.tan(vertical) * camera.aspect);
      const distance = radius / Math.sin(Math.min(vertical, horizontal)) * 1.12;
      controls.target.copy(center);
      camera.position.copy(center).add(new THREE.Vector3(.65, -1, .65).normalize().multiplyScalar(distance));
      controls.update();
      draw();
    }
    function update(fit = false) {
      bounds = new THREE.Box3();
      let visible = 0;
      let added = 0;
      for (const group of groups.values()) {
        let n = 0;
        for (const item of group.items) {
          if (scope.value === 'step' && item.step > currentStep) continue;
          group.mesh.setMatrixAt(n, item.transform);
          color.set(scope.value === 'step' && item.step < currentStep ? '#abb3bb' : item.color);
          group.mesh.setColorAt(n++, color);
          bounds.union(item.bounds);
          visible++;
          if (item.step === currentStep) added++;
        }
        group.mesh.count = n;
        group.mesh.instanceMatrix.needsUpdate = true;
        if (group.mesh.instanceColor) group.mesh.instanceColor.needsUpdate = true;
      }
      status.textContent = scope.value === 'full'
        ? `Complete model · ${visible} pieces`
        : `Step ${currentStep + 1} · ${visible} pieces assembled · ${added} new pieces in color`;
      if (fit) reset();
      draw();
    }
    const resize = () => {
      if (host.hidden || !host.clientWidth) return;
      renderer.setSize(host.clientWidth, host.clientHeight, false);
      camera.aspect = host.clientWidth / host.clientHeight;
      camera.updateProjectionMatrix();
      draw();
    };
    new ResizeObserver(resize).observe(host);
    function setView(is3d) {
      host.hidden = !is3d;
      get('assembly').hidden = is3d;
      get('viewer-help').hidden = !is3d;
      scope.disabled = !is3d;
      get('model-reset').disabled = !is3d;
      get('view-3d').setAttribute('aria-pressed', String(is3d));
      get('view-image').setAttribute('aria-pressed', String(!is3d));
      status.hidden = !is3d;
      resize();
    }
    get('view-3d').onclick = () => setView(true);
    get('view-image').onclick = () => setView(false);
    get('model-reset').onclick = reset;
    scope.onchange = () => update(true);
    canvas.addEventListener('keydown', event => {
      if (event.key === 'Home') { event.preventDefault(); reset(); }
      if (['+', '=', '-', '−'].includes(event.key)) {
        event.preventDefault();
        const zoom = event.key === '+' || event.key === '=' ? .85 : 1.18;
        camera.position.sub(controls.target).multiplyScalar(zoom).add(controls.target);
        controls.update();
      }
    });
    canvas.addEventListener('webglcontextlost', event => {
      event.preventDefault();
      illustrationOnly('The 3D view paused. Reload to restore it, or continue with the step illustrations.');
    });
    window.maxViewer = {setStep(step) {
      currentStep = step;
      scope.value = 'step';
      update();
    }};
    resize();
    update(true);
  } catch (error) {
    renderer?.dispose();
    illustrationOnly('3D is unavailable in this browser. The step illustrations are still available.');
    console.error('Max viewer:', error);
  }
})();
