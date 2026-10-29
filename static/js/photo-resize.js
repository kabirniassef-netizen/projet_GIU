// Réduit dans le navigateur les photos trop lourdes (galerie du téléphone) avant l'envoi.
const MAX_PHOTO_SIZE = 5 * 1024 * 1024;

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Image illisible')); };
    image.src = url;
  });
}

// Renvoie la photo telle quelle si elle respecte la limite, sinon une version JPEG redimensionnée.
async function preparePhoto(file) {
  if (!file || file.size <= MAX_PHOTO_SIZE) return file;
  try {
    const image = await loadImage(file);
    const name = file.name.replace(/\.[^.]+$/, '') + '.jpg';
    for (const [maxSide, quality] of [[2560, 0.85], [1920, 0.8], [1280, 0.75]]) {
      const scale = Math.min(1, maxSide / Math.max(image.naturalWidth, image.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(image.naturalWidth * scale);
      canvas.height = Math.round(image.naturalHeight * scale);
      canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', quality));
      if (blob && blob.size <= MAX_PHOTO_SIZE) return new File([blob], name, { type: 'image/jpeg' });
    }
  } catch (error) { /* format non lisible par le navigateur : on garde l'original */ }
  return file;
}

// Bouton « Prendre une photo » (data-camera-for="id du champ photo") : affiché sur les écrans tactiles,
// il ouvre directement l'appareil photo et place le cliché dans le champ photo habituel.
document.addEventListener('DOMContentLoaded', () => {
  if (!window.matchMedia('(pointer: coarse)').matches || typeof DataTransfer === 'undefined') return;
  document.querySelectorAll('[data-camera-for]').forEach(button => {
    const photoInput = document.getElementById(button.dataset.cameraFor);
    const camera = Object.assign(document.createElement('input'), { type: 'file', accept: 'image/*', hidden: true });
    camera.setAttribute('capture', 'environment');
    button.after(camera);
    button.hidden = false;
    button.addEventListener('click', () => camera.click());
    camera.addEventListener('change', () => {
      if (!camera.files[0]) return;
      const transfer = new DataTransfer();
      transfer.items.add(camera.files[0]);
      photoInput.files = transfer.files;
      camera.value = '';
      photoInput.dispatchEvent(new Event('change'));
    });
  });
});
