/**
 * Publications Carousel
 * Responsive carousel for displaying publication cards with PDF-extracted figures
 */

interface Publication {
  paperId: string | null;
  title: string;
  titleHtml?: string;
  semanticScholarUrl: string;
  authors: string;
  journal: string;
  citations: number;
  year: number | null;
  figureUrl: string | null;
  fallbackGradient: string;
}

interface PublisherGradients {
  [key: string]: string;
}

const PUBLISHER_GRADIENTS: PublisherGradients = {
  'Nature': 'linear-gradient(135deg, #0d47a1, #1976d2)',
  'Biorxiv': 'linear-gradient(135deg, #ff6f00, #ff8f00)',
  'arXiv': 'linear-gradient(135deg, #b31b1b, #c62828)',
  'Journal of Open Source Software': 'linear-gradient(135deg, #1565c0, #1976d2)',
  'Accounts of Chemical Research': 'linear-gradient(135deg, #2e7d32, #388e3c)',
  'default': 'linear-gradient(135deg, #455a64, #607d8b)'
};

const JOURNAL_ABBREVIATIONS: { [key: string]: string } = {
  'Journal of Open Source Software': 'JOSS',
  'Accounts of Chemical Research': 'Acc. Chem. Res.',
  'Journal of Chemical Theory and Computation': 'J. Chem. Theory Comput.',
  'Journal of Physical Chemistry': 'J. Phys. Chem.',
  'Journal of Chemical Physics': 'J. Chem. Phys.',
  'Proceedings of the National Academy of Sciences': 'PNAS',
  'Journal of the American Chemical Society': 'JACS',
  'Nature Communications': 'Nat. Commun.',
  'Nature Methods': 'Nat. Methods',
  'Nature Chemistry': 'Nat. Chem.',
  'Physical Review Letters': 'Phys. Rev. Lett.',
};

/**
 * Abbreviate journal name if it has more than 3 words
 */
function abbreviateJournal(journalName: string): string {
  // Check if we have a known abbreviation
  if (JOURNAL_ABBREVIATIONS[journalName]) {
    return JOURNAL_ABBREVIATIONS[journalName];
  }

  // Count words in journal name
  const words = journalName.trim().split(/\s+/);

  // If 3 or fewer words, keep as is
  if (words.length <= 3) {
    return journalName;
  }

  // For unknown journals with >3 words, create abbreviation from first letters
  const abbreviation = words
    .map(word => {
      // Skip common words like "of", "the", "and"
      const skipWords = ['of', 'the', 'and', 'in', 'on', 'for', 'with'];
      if (skipWords.includes(word.toLowerCase())) {
        return '';
      }
      return word[0].toUpperCase();
    })
    .filter(letter => letter)
    .join('');

  return abbreviation || journalName; // Fallback to full name if abbreviation fails
}

/**
 * Apply figure or fallback gradient to publication card
 */
function applyFigureOrFallback(pub: Publication, index: number): void {
  const $figure = $(`.publication-card-figure[data-figure-container="${index}"]`);
  $figure.removeClass('loading');

  if (pub.figureUrl) {
    const img = new Image();
    img.onload = function() {
      $figure.html(`<img src="${pub.figureUrl}" alt="${pub.title || 'Publication figure'}">`);
    };
    img.onerror = function() {
      const gradient = pub.fallbackGradient || PUBLISHER_GRADIENTS[pub.journal] || PUBLISHER_GRADIENTS.default;
      $figure.addClass('fallback').css('background', gradient);
    };
    img.src = pub.figureUrl;
  } else {
    const gradient = pub.fallbackGradient || PUBLISHER_GRADIENTS[pub.journal] || PUBLISHER_GRADIENTS.default;
    $figure.addClass('fallback').css('background', gradient);
  }
}

/**
 * Create publication card HTML
 */
function createPublicationCard(pub: Publication, index: number): string {
  const url = pub.semanticScholarUrl || '#';
  const title = pub.title || (pub.titleHtml ? pub.titleHtml.replace(/<[^>]*>/g, '') : '');

  return `
    <a href="${url}" class="publication-card" data-card-index="${index}" target="_blank" rel="noopener noreferrer">
      <div class="publication-card-figure loading" data-figure-container="${index}"></div>
      <div class="publication-card-content">
        <div class="publication-card-title">${title}</div>
        <div class="publication-card-authors">${pub.authors}</div>
        <div class="publication-card-meta">
          <div class="publication-card-journal">${abbreviateJournal(pub.journal)}</div>
          <div class="publication-card-year">${pub.year || ''}</div>
          <div class="publication-card-citations">${(pub.citations || 0).toLocaleString()} citations</div>
        </div>
      </div>
    </a>
  `;
}

/**
 * Get number of cards visible per viewport based on CSS breakpoints
 */
function getCardsPerView(): number {
  const width = window.innerWidth;
  if (width <= 600) return 1;
  if (width <= 900) return 2;
  return 3;
}

/**
 * Initialize carousel navigation with responsive pagination
 */
function initCarouselNavigation(totalCards: number): void {
  let currentIndex = 0;
  let cardsPerView = getCardsPerView();
  let maxIndex = Math.ceil(totalCards / cardsPerView) - 1;

  function updateCarousel(): void {
    // Recalculate in case viewport changed
    cardsPerView = getCardsPerView();
    maxIndex = Math.ceil(totalCards / cardsPerView) - 1;

    // Ensure currentIndex is within bounds after resize
    if (currentIndex > maxIndex) {
      currentIndex = maxIndex;
    }

    // Each card takes (cardWidth + gap) space in the track
    // Slide by cardsPerView * (cardWidth + gap) to align next page
    const cardWidth = 240;
    const gap = 16;
    const slideWidth = cardsPerView * (cardWidth + gap);
    const offset = -currentIndex * slideWidth;

    $('.publications-carousel-track').css('transform', `translateX(${offset}px)`);

    // Scope to Publications carousel dots only
    $('.publications-carousel-dots .carousel-dot').removeClass('active');
    $(`.publications-carousel-dots .carousel-dot[data-index="${currentIndex}"]`).addClass('active');
  }

  function goToSlide(index: number): void {
    // Recalculate maxIndex
    cardsPerView = getCardsPerView();
    maxIndex = Math.ceil(totalCards / cardsPerView) - 1;

    // Wrap around at edges
    if (index < 0) {
      currentIndex = maxIndex;
    } else if (index > maxIndex) {
      currentIndex = 0;
    } else {
      currentIndex = index;
    }
    updateCarousel();
  }

  // Update dots based on current viewport
  function updateDots(): void {
    cardsPerView = getCardsPerView();
    const numPages = Math.ceil(totalCards / cardsPerView);

    // Clear existing dots
    $('.publications-carousel-dots').empty();

    // Generate new dots
    for (let i = 0; i < numPages; i++) {
      const isActive = i === currentIndex && i <= Math.ceil(totalCards / cardsPerView) - 1;
      const dot = `<div class="carousel-dot ${isActive ? 'active' : ''}" data-index="${i}"></div>`;
      $('.publications-carousel-dots').append(dot);
    }

    // Ensure currentIndex is valid
    if (currentIndex > numPages - 1) {
      currentIndex = numPages - 1;
    }

    updateCarousel();
  }

  // Arrow navigation - scope to publications carousel buttons
  $('.publications-carousel-btn.carousel-prev').on('click', function() {
    goToSlide(currentIndex - 1);
  });

  $('.publications-carousel-btn.carousel-next').on('click', function() {
    goToSlide(currentIndex + 1);
  });

  // Dot navigation - dots now represent pages, so data-index is the page index
  $('.publications-carousel-dots').on('click', '.carousel-dot', function() {
    const pageIndex = parseInt($(this).data('index') as string);
    goToSlide(pageIndex);
  });

  // Touch/swipe support
  let touchStartX = 0;
  let touchEndX = 0;

  $('.publications-carousel-track').on('touchstart', function(e: JQuery.TouchStartEvent) {
    const touch = (e.originalEvent as TouchEvent).changedTouches[0];
    touchStartX = touch.screenX;
  });

  $('.publications-carousel-track').on('touchend', function(e: JQuery.TouchEndEvent) {
    const touch = (e.originalEvent as TouchEvent).changedTouches[0];
    touchEndX = touch.screenX;
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > swipeThreshold) {
      if (diff > 0) {
        goToSlide(currentIndex + 1);
      } else {
        goToSlide(currentIndex - 1);
      }
    }
  });

  // Keyboard navigation
  $(document).on('keydown', function(e: JQuery.KeyDownEvent) {
    if ($('.publications-carousel:visible').length > 0) {
      if (e.key === 'ArrowLeft') {
        goToSlide(currentIndex - 1);
      } else if (e.key === 'ArrowRight') {
        goToSlide(currentIndex + 1);
      }
    }
  });

  // Window resize handler
  let resizeTimer: ReturnType<typeof setTimeout>;
  $(window).on('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
      updateDots();
    }, 150); // Debounce resize events
  });

  // Initialize dots
  updateDots();
}

/**
 * Initialize the publications carousel
 */
export async function initPublicationsCarousel(): Promise<void> {
  console.log('Carousel initializing...');

  try {
    const response = await fetch('/static/files/publications.json');

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const publications: Publication[] = await response.json();
    console.log('Loaded publications from JSON:', publications.length);

    // Add cards
    publications.forEach((pub, index) => {
      const card = createPublicationCard(pub, index);
      $('.publications-carousel-track').append(card);
      applyFigureOrFallback(pub, index);
    });

    // Initialize carousel (dots will be created inside)
    initCarouselNavigation(publications.length);

  } catch (error) {
    console.error('Error loading publications JSON:', error);
    // Display error message to user
    $('.publications-carousel-track').html(
      '<div style="padding: 40px; text-align: center; color: rgba(10, 10, 10, 0.6);">' +
      'Unable to load publications. Please try again later.' +
      '</div>'
    );
  }
}

// Auto-initialize when DOM is ready
$(() => {
  initPublicationsCarousel();
});
