const fileInput = document.getElementById('fileInput');
const extractBtn = document.getElementById('extractBtn');
const output = document.getElementById('output');
const fileNameEl = document.getElementById('fileName');
const statusEl = document.getElementById('status');
const loaderOverlay = document.getElementById('loaderOverlay');
const canvas = document.getElementById('threeCanvas');

let renderer, scene, camera, torus, animId;

function initThree() {
  renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
  resizeCanvas();
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.z = 3.5;

  const geom = new THREE.TorusGeometry(0.9, 0.25, 32, 100);
  const mat = new THREE.MeshStandardMaterial({ color: 0x00d4ff, emissive: 0x006d91, metalness: 0.7, roughness: 0.25 });
  torus = new THREE.Mesh(geom, mat);
  scene.add(torus);

  const p1 = new THREE.PointLight(0xffffff, 0.9);
  p1.position.set(4,4,4);
  scene.add(p1);

  const amb = new THREE.AmbientLight(0x223344, 0.6);
  scene.add(amb);
}

function resizeCanvas(){
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setSize(w, h);
  if (camera) camera.aspect = w/h;
  if (camera) camera.updateProjectionMatrix();
}

function animateThree(){
  animId = requestAnimationFrame(animateThree);
  torus.rotation.x += 0.01;
  torus.rotation.y += 0.015;
  renderer.render(scene, camera);
}

function showLoader(){
  if (!renderer) initThree();
  loaderOverlay.style.display = 'flex';
  resizeCanvas();
  animateThree();
}

function hideLoader(){
  cancelAnimationFrame(animId);
  loaderOverlay.style.display = 'none';
}

window.addEventListener('resize', () => {
  if (renderer) resizeCanvas();
});

extractBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    statusEl.textContent = 'Select an image first.';
    output.textContent = ' File Not Selected';
    return;
  }

  fileNameEl.textContent = file.name;
  statusEl.textContent = 'Preparing upload...';
  output.textContent = '';

  const formData = new FormData();
  formData.append('file', file);

  try {
    showLoader();
    statusEl.textContent = 'Uploading & extractiing';

    const resp = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(errText || `HTTP ${resp.status}`);
    }

    const data = await resp.json();

    hideLoader();

    if (Object.keys(data).length === 1 && data.extracted_text !== undefined) {
      const text = data.extracted_text.trim();
      statusEl.textContent = 'Extraction finished ';
      output.textContent = text || '(no text found)';
    } else {
      statusEl.textContent = 'Extraction finished (structured).';
      const lines = [];
      for (const [k, v] of Object.entries(data)) {
        lines.push(`${k} = ${v}`);
      }
      output.textContent = lines.join('\n');
    }
  } catch (err) {
    hideLoader();
    statusEl.textContent = 'Error during extraction.';
    output.textContent = 'Error ' + (err.message || err);
    console.error(err);
  }
});
