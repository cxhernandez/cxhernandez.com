/**
 * Photography Carousel
 * Auto-advancing carousel with Instagram embeds, touch/swipe support, and dot navigation.
 */

declare const instgrm: { Embeds: { process: () => void } } | undefined;

const AUTO_ADVANCE_DURATION = 8000; // 8 seconds

let currentSlide = 0;
let totalSlides = 0;
let autoAdvanceInterval: ReturnType<typeof setInterval> | null = null;
let progressInterval: ReturnType<typeof setInterval> | null = null;
let touchStartX = 0;
let touchEndX = 0;

function startAutoAdvance(): void {
  if (autoAdvanceInterval) clearInterval(autoAdvanceInterval);
  if (progressInterval) clearInterval(progressInterval);

  const progressBar = document.getElementById('carouselProgress');
  if (progressBar) {
    progressBar.style.transition = 'none';
    progressBar.style.width = '0%';
    // Force reflow
    progressBar.offsetHeight;
    progressBar.style.transition = `width ${AUTO_ADVANCE_DURATION}ms linear`;
    progressBar.style.width = '100%';
  }

  autoAdvanceInterval = setInterval(() => {
    moveCarousel(1);
  }, AUTO_ADVANCE_DURATION);
}

function stopAutoAdvance(): void {
  if (autoAdvanceInterval) {
    clearInterval(autoAdvanceInterval);
    autoAdvanceInterval = null;
  }
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }

  const progressBar = document.getElementById('carouselProgress');
  if (progressBar) {
    progressBar.style.transition = 'none';
    progressBar.style.width = '0%';
  }
}

function handleTouchStart(e: Event): void {
  const touch = e as TouchEvent;
  touchStartX = touch.changedTouches[0].screenX;
}

function handleTouchEnd(e: Event): void {
  const touch = e as TouchEvent;
  touchEndX = touch.changedTouches[0].screenX;
  handleSwipe();
}

function handleSwipe(): void {
  const swipeThreshold = 50;
  const diff = touchStartX - touchEndX;

  if (Math.abs(diff) > swipeThreshold) {
    if (diff > 0) {
      moveCarousel(1);
    } else {
      moveCarousel(-1);
    }
  }
}

function updateCarousel(): void {
  const track = document.getElementById('carouselTrack');
  if (track) {
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
  }

  document.querySelectorAll('#carouselDots .carousel-dot').forEach((dot, i) => {
    dot.className = 'carousel-dot' + (i === currentSlide ? ' active' : '');
  });

  if (autoAdvanceInterval) {
    startAutoAdvance();
  }
}

function moveCarousel(direction: number): void {
  if (totalSlides === 0) return;
  currentSlide = (currentSlide + direction + totalSlides) % totalSlides;
  updateCarousel();
}

function goToSlide(index: number): void {
  if (index === currentSlide) return;
  currentSlide = index;
  updateCarousel();
}

async function initCarousel(): Promise<void> {
  const track = document.getElementById('carouselTrack');
  const dotsContainer = document.getElementById('carouselDots');
  const carousel = document.querySelector('.photo-carousel');
  const carouselContainer = document.querySelector('.carousel-container');

  if (!track || !dotsContainer) return;

  const photosJsonUrl = carousel?.getAttribute('data-photos-json');
  if (!photosJsonUrl) return;

  try {
    const response = await fetch(photosJsonUrl);
    if (!response.ok) throw new Error('Failed to load photos.json');

    const data = await response.json();
    const photos: string[] = data.photos || [];

    totalSlides = photos.length;

    if (totalSlides === 0) {
      track.innerHTML =
        '<div class="carousel-slide"><p class="carousel-fallback">No photos yet. <a href="https://www.instagram.com/cxhrndz/" class="carousel-fallback-link">Visit Instagram &rarr;</a></p></div>';
      return;
    }

    track.innerHTML = '';

    photos.forEach((url, index) => {
      const slide = document.createElement('div');
      slide.className = 'carousel-slide';

      const wrapper = document.createElement('div');
      wrapper.className = 'instagram-embed-wrapper';

      const blockquote = document.createElement('blockquote');
      blockquote.className = 'instagram-media';
      blockquote.setAttribute('data-instgrm-permalink', url);
      blockquote.setAttribute('data-instgrm-version', '14');

      wrapper.appendChild(blockquote);
      slide.appendChild(wrapper);
      track.appendChild(slide);

      const dot = document.createElement('span');
      dot.className = 'carousel-dot' + (index === 0 ? ' active' : '');
      dot.addEventListener('click', () => goToSlide(index));
      dotsContainer.appendChild(dot);
    });

    // Process Instagram embeds
    setTimeout(() => {
      if (typeof instgrm !== 'undefined') {
        instgrm.Embeds.process();
      }
    }, 100);

    // Start auto-advance after embeds load
    setTimeout(() => {
      startAutoAdvance();
    }, 2000);

    // Pause auto-advance on hover
    if (carousel) {
      carousel.addEventListener('mouseenter', stopAutoAdvance);
      carousel.addEventListener('mouseleave', startAutoAdvance);
    }

    // Touch/swipe support
    if (carouselContainer) {
      carouselContainer.addEventListener('touchstart', handleTouchStart, false);
      carouselContainer.addEventListener('touchend', handleTouchEnd, false);
    }
  } catch (error) {
    console.error('Error loading photos:', error);
    if (track) {
      track.innerHTML =
        '<div class="carousel-slide"><p class="carousel-fallback">Unable to load photos. <a href="https://www.instagram.com/cxhrndz/" class="carousel-fallback-link">Visit Instagram &rarr;</a></p></div>';
    }
  }
}

// Attach button listeners (scoped to .photo-carousel to avoid conflicts with other carousels)
function initButtons(): void {
  const carousel = document.querySelector('.photo-carousel');
  if (!carousel) return;
  carousel.querySelector('.carousel-prev')?.addEventListener('click', () => moveCarousel(-1));
  carousel.querySelector('.carousel-next')?.addEventListener('click', () => moveCarousel(1));
}

// Initialize
function init(): void {
  initButtons();
  initCarousel();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

export {};
