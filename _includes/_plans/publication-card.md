# Plan: Mobile-Friendly Publications Section

## Current State

The publications section uses a DataTable with 6 columns (index, title, authors, journal, citations, year) and 12 entries. On mobile, it currently:
- Uses horizontal scrolling with `-webkit-overflow-scrolling: touch`
- Reduces font sizes to 12-14px
- Shrinks columns to 150px max-width with 6px padding
- Becomes cramped and difficult to read on small screens

**Key Files:**
- [_includes/Publications.html](_includes/Publications.html) - Template with DataTables initialization
- [_includes/publications.md](_includes/publications.md) - Table data (modified in git status)
- [_sass/_custom.scss](_sass/_custom.scss) - Publications styles (lines 981-1199)

## Design Options

### Option 1: Card-Based Layout (Recommended)

**What it does:** Transforms the table into individual cards on mobile (≤600px), similar to the Software section pattern already used on the site.

**Visual hierarchy:**
- Title (bold, 16px) - most prominent
- Authors (14px, truncated to 2 lines)
- Journal • Year (inline metadata)
- Citations badge with star icon

**Pros:**
- ✅ Matches existing Software section design pattern
- ✅ Highly readable, no horizontal scrolling
- ✅ Touch-friendly with large tap targets
- ✅ Clear visual hierarchy
- ✅ Design consistency across sections

**Cons:**
- ❌ Requires dual HTML structure (table + cards)
- ❌ Higher maintenance burden
- ❌ DataTables features need custom implementation for cards
- ❌ More vertical scrolling

### Option 2: Expandable List Layout

**What it does:** Compact list where each publication is collapsible. Tap to expand full details.

**Collapsed state:** Title (2 lines) + Year • Journal
**Expanded state:** Full title + authors + citations + Semantic Scholar link

**Pros:**
- ✅ Compact vertical space
- ✅ Progressive disclosure reduces cognitive load
- ✅ Good for browsing many items

**Cons:**
- ❌ Requires interaction to see details
- ❌ Citations hidden when collapsed
- ❌ Pattern not used elsewhere on site

### Option 3: Hybrid (Table + Cards with DataTables)

**What it does:** Like Option 1 but uses DataTables API to power card search/pagination on mobile.

**Pros:**
- ✅ Preserves all DataTables features on mobile
- ✅ Single source of truth
- ✅ Card readability + table functionality

**Cons:**
- ❌ Highest implementation complexity
- ❌ Performance overhead (DataTables runs when hidden)
- ❌ Largest code footprint

### Option 4: Enhanced Horizontal Scrolling

**What it does:** Keeps the table but improves UX with scroll fade indicators, sticky title column, hidden authors column on mobile, better touch targets.

**Pros:**
- ✅ Minimal code changes
- ✅ Preserves all features
- ✅ Low risk

**Cons:**
- ❌ Doesn't solve "busy" feeling
- ❌ Still requires horizontal scrolling
- ❌ Hides data (authors column)

## Final Recommendation

**Horizontal Carousel with Europe PMC Figures and Gradient Fallbacks**

This approach replaces the DataTable entirely with a responsive carousel:
- **Desktop:** 3 publication cards visible at once
- **Mobile:** 1 card at a time with swipe gestures
- **Figures:** Real paper figures from Europe PMC where available, publisher-branded gradients as fallback
- **Navigation:** Arrows, dots, swipe, and keyboard support

This provides the most engaging, visual experience while solving the "busy on mobile" problem.

## Adding Visual Elements to Cards

The Semantic Scholar API **does not provide access to paper figures or images**. However, several alternatives exist for adding visual interest to publication cards:

### Visual Options

#### Option A: Europe PMC/PubMed Central Figures (Automated, Some Papers)
**What it provides:** Actual paper figure thumbnails from open-access repositories

**How it works:**
- Europe PMC provides figure thumbnails for papers with appropriate licenses
- Requires cross-referencing DOI/PMID for each publication
- Only works for papers available in these repositories (likely: Nature paper, some BioRxiv papers)

**Implementation:**
- Make API calls to Europe PMC for each publication
- Extract thumbnail URLs from API responses
- Fall back to placeholder for papers without figures

**Pros:** ✅ Real paper figures, professional appearance
**Cons:** ❌ Complex implementation, won't work for all papers (arXiv, JOSS papers likely unavailable)

#### Option B: Generated Gradients Based on Data (Automated, All Papers)
**What it provides:** Unique gradient backgrounds for each card based on publication metadata

**How it works:**
- Generate color gradients using year + citation count as seeds
- Each publication gets a distinctive visual identity
- Example: 2014 paper with 2072 citations → blue-purple gradient

**Implementation:**
```javascript
function generateGradient(year, citations) {
  const hue1 = (year - 2010) * 20 % 360;
  const hue2 = (hue1 + (citations % 180)) % 360;
  return `linear-gradient(135deg, hsl(${hue1}, 70%, 85%), hsl(${hue2}, 70%, 75%))`;
}
```

**Pros:** ✅ Simple, works for all papers, unique per publication, no external dependencies
**Cons:** ❌ Abstract rather than representative of content

#### Option C: Citation Count Visualization (Automated, All Papers)
**What it provides:** Simple bar chart or spark-line showing citation impact

**How it works:**
- Visual bar scaled relative to max citations (2072 for MDTraj)
- Creates instant visual hierarchy by citation count
- Could use mini chart showing citation trend if data available

**Pros:** ✅ Informative, helps users quickly identify high-impact papers
**Cons:** ❌ Single-dimensional visualization, requires additional styling

#### Option D: Field Icons/Badges (Semi-Automated)
**What it provides:** Icon representing research domain (ML, chemistry, biology, etc.)

**How it works:**
- Semantic Scholar API provides `fieldsOfStudy` or `s2FieldsOfStudy`
- Map fields to icons (🧬 biology, 🧪 chemistry, 🤖 ML, 📊 data science)
- Display as badge in corner or header

**Pros:** ✅ Helpful categorization, professional appearance
**Cons:** ❌ Generic icons, requires icon library or emoji

#### Option E: Manual Curation (Manual, Select Papers)
**What it provides:** Hand-picked figure or graphic for each publication

**How it works:**
- Add `image_url` field to each publication in data file
- Manually curate best figure from each paper
- Provides complete control over visual quality

**Pros:** ✅ Highest quality, full control, most representative
**Cons:** ❌ Labor-intensive, requires updates for new papers, manual maintenance

### Recommended Approach: **Option A (Europe PMC Figures) with Publisher Logo + Gradient Fallback**

**Why this approach:**
1. Provides real paper figures where available (most professional appearance)
2. Graceful fallback to publisher logos with branded gradients
3. Creates visual interest while being content-representative
4. Combines automated figure fetching with styled fallbacks

**Carousel design with figures:**
```
        ◀                                        ▶
┌─────────────────────────────────────────────────┐
│ [Paper Figure - 280px height]                  │ ← Real figure from PMC/EPMC
│  (or Publisher Logo + Gradient)                 │   (or fallback)
│                                                  │
│ Title (bold, 18px)                              │
│ Authors (14px, truncated to 2 lines)           │
│ Journal • Year • ⭐ 2072 citations             │
└─────────────────────────────────────────────────┘
         ● ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○

← Swipe to navigate →
```

**Implementation strategy:**
1. Horizontal carousel similar to Photography section
2. Extract DOIs/PMIDs from Semantic Scholar URLs
3. Query Europe PMC API for figure thumbnails asynchronously
4. If figures unavailable, use publisher-branded gradient
5. Touch-friendly swipe gestures + arrow navigation
6. Pagination dots for all 12 publications

## Implementation Steps

### 1. Create Mobile Carousel Styles in _custom.scss

Add carousel styles in the `section#Publications` block (after line 1199):

```scss
// Publications carousel (replaces DataTable entirely)
.publications-carousel {
  display: block;
  position: relative;
  padding: 40px 0;
  margin: 40px auto;
  max-width: 1200px;

  @media screen and (max-width: 600px) {
    padding: 0;
    margin: 40px 0;
  }
}

.publications-carousel-container {
  position: relative;
  width: 100%;
  margin: 0 auto;
  overflow: hidden;
  padding: 0 60px; // Space for navigation arrows

  @media screen and (max-width: 600px) {
    max-width: 400px;
    padding: 0 50px;
  }

  @media screen and (max-width: 480px) {
    padding: 0 35px;
  }
}

.publications-carousel-track {
  display: flex;
  gap: 24px;
  transition: transform var(--duration-slow) var(--ease-out-expo);
  touch-action: pan-y pinch-zoom;

  @media screen and (max-width: 600px) {
    gap: 0;
  }
}

.publication-card {
  flex: 0 0 calc(33.333% - 16px); // 3 cards on desktop with gap
  background: var(--surface-raised);
  border: 2px solid rgba(10, 10, 10, 0.06);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px var(--shadow-subtle);
  transition: all var(--duration-base) ease;

  @media screen and (max-width: 600px) {
    flex: 0 0 100%; // 1 card on mobile
    min-width: 100%;
  }

  @media (hover: hover) {
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }
  }

  &:active {
    box-shadow: 0 2px 12px var(--shadow-subtle);
  }
}

// Figure container (real figure or fallback)
.publication-card-figure {
  width: 100%;
  height: 280px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  overflow: hidden;

  @media screen and (max-width: 400px) {
    height: 240px;
  }

  // For fallback state (publisher logo + gradient)
  &.fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    background-size: auto 40%;  // Scale down logo
  }

  // Loading shimmer effect
  &.loading {
    background: linear-gradient(
      90deg,
      rgba(10, 10, 10, 0.03) 0%,
      rgba(10, 10, 10, 0.06) 50%,
      rgba(10, 10, 10, 0.03) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.publication-card-content {
  padding: 24px 20px;

  @media screen and (max-width: 400px) {
    padding: 20px 16px;
  }
}

.publication-card-title {
  font-family: var(--font-display);
  font-size: 18px;
  line-height: 1.3;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--ink);

  @media screen and (max-width: 400px) {
    font-size: 16px;
  }

  a {
    color: var(--ink);
    text-decoration: none;

    &:active {
      color: var(--accent-primary);
    }
  }
}

.publication-card-authors {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.5;
  color: rgba(10, 10, 10, 0.7);
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;

  @media screen and (max-width: 400px) {
    font-size: 13px;
  }
}

.publication-card-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 13px;
  color: rgba(10, 10, 10, 0.6);

  @media screen and (max-width: 400px) {
    font-size: 12px;
  }

  .publication-card-journal {
    font-weight: 600;
  }

  .publication-card-year {
    &::before {
      content: '•';
      margin-right: 8px;
      color: rgba(10, 10, 10, 0.3);
    }
  }

  .publication-card-citations {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-weight: 600;
    color: var(--accent-primary);

    &::before {
      content: '• ⭐';
      margin-right: 4px;
    }
  }
}

// Carousel navigation arrows (reuse Photography section pattern)
.publications-carousel-btn {
  position: absolute;
  top: 140px; // Center on figure
  transform: translateY(-50%);
  z-index: 10;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--surface-raised);
  border: 2px solid rgba(10, 10, 10, 0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px var(--shadow-subtle);
  transition: all var(--duration-base) var(--ease-out-expo);

  @media screen and (max-width: 480px) {
    width: 32px;
    height: 32px;
  }

  @media screen and (max-width: 400px) {
    width: 30px;
    height: 30px;
  }

  svg {
    width: 20px;
    height: 20px;
    transition: transform var(--duration-fast) ease;

    @media screen and (max-width: 480px) {
      width: 16px;
      height: 16px;
    }
  }

  &:active {
    transform: translateY(-50%) scale(0.95);
    background: var(--accent-primary);
    color: var(--paper);
    border-color: var(--accent-primary);
  }

  &.carousel-prev {
    left: 0;
  }

  &.carousel-next {
    right: 0;
  }

  @media (hover: hover) {
    &:hover {
      background: var(--accent-primary);
      color: var(--paper);
      border-color: var(--accent-primary);
      box-shadow: 0 6px 20px rgba(43, 75, 255, 0.3);
      transform: translateY(-50%) scale(1.1);

      svg {
        transform: scale(1.1);
      }
    }
  }
}

// Carousel dots (reuse Photography section pattern)
.publications-carousel-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 24px;

  @media screen and (max-width: 400px) {
    gap: 6px;
    margin-top: 20px;
  }
}

.carousel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(10, 10, 10, 0.2);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out-expo);
  border: 2px solid transparent;

  @media screen and (max-width: 400px) {
    width: 6px;
    height: 6px;
  }

  &.active {
    background: var(--accent-primary);
    transform: scale(1.3);
    box-shadow: 0 2px 8px rgba(43, 75, 255, 0.4);
  }

  &:active:not(.active) {
    background: rgba(10, 10, 10, 0.4);
    transform: scale(1.15);
  }

  @media (hover: hover) {
    &:hover:not(.active) {
      background: rgba(10, 10, 10, 0.4);
      transform: scale(1.15);
    }
  }
}
```

### 2. Hide DataTable on All Screens

Update existing responsive styles in _custom.scss (around lines 1100-1150):

```scss
section#Publications {
  .dataTables_wrapper {
    display: none; // Hide DataTables entirely, use carousel instead
  }
}
```

### 3. Generate Carousel HTML with Europe PMC Figures

Add carousel structure to Publications.html (after the table include, before closing `</section>`):

```html
<div class="publications-carousel">
  <div class="publications-carousel-container">
    <!-- Previous button -->
    <button class="publications-carousel-btn carousel-prev" aria-label="Previous publication">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
    </button>

    <!-- Carousel track -->
    <div class="publications-carousel-track">
      <!-- Cards will be generated dynamically by JavaScript -->
    </div>

    <!-- Next button -->
    <button class="publications-carousel-btn carousel-next" aria-label="Next publication">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 18l6-6-6-6"/>
      </svg>
    </button>
  </div>

  <!-- Pagination dots -->
  <div class="publications-carousel-dots">
    <!-- Dots will be generated dynamically by JavaScript -->
  </div>
</div>

<script>
// Publisher-specific gradients for fallback
const publisherGradients = {
  'Nature': 'linear-gradient(135deg, #0d47a1, #1976d2)',
  'Biorxiv': 'linear-gradient(135deg, #ff6f00, #ff8f00)',
  'arXiv': 'linear-gradient(135deg, #b31b1b, #c62828)',
  'Journal of Open Source Software': 'linear-gradient(135deg, #1565c0, #1976d2)',
  'Accounts of Chemical Research': 'linear-gradient(135deg, #2e7d32, #388e3c)',
  'default': 'linear-gradient(135deg, #455a64, #607d8b)'
};

// Extract paper ID from Semantic Scholar URL
function extractPaperId(semanticScholarUrl) {
  const match = semanticScholarUrl.match(/\/paper\/([a-f0-9]+)/);
  return match ? match[1] : null;
}

// Fetch figure from Europe PMC (via Semantic Scholar paper ID)
async function fetchPaperFigure(paperId) {
  try {
    // Get paper details from Semantic Scholar to find external IDs (DOI, PMID)
    const s2Response = await fetch(`https://api.semanticscholar.org/graph/v1/paper/${paperId}?fields=externalIds,openAccessPdf`);
    if (!s2Response.ok) return null;

    const s2Data = await s2Response.json();
    const pmid = s2Data.externalIds?.PubMed;
    const pmcid = s2Data.externalIds?.PubMedCentral;

    // Try Europe PMC if we have PMID or PMCID
    if (pmid || pmcid) {
      const id = pmcid || pmid;
      const source = pmcid ? 'PMC' : 'MED';
      const epmcResponse = await fetch(`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=ext_id:${id}&format=json`);

      if (epmcResponse.ok) {
        const epmcData = await epmcResponse.json();
        const result = epmcData.resultList?.result?.[0];

        // Check if full text is available
        if (result?.hasTextMinedTerms === 'Y' && result?.inEPMC === 'Y') {
          // Try to get figure from full text
          const pmcId = result.pmcid;
          if (pmcId) {
            // Europe PMC figure URL pattern (first figure)
            return `https://europepmc.org/articles/${pmcId}/bin/${pmcId}-g001.jpg`;
          }
        }
      }
    }

    return null;
  } catch (error) {
    console.warn('Error fetching figure:', error);
    return null;
  }
}

// Create fallback image with publisher logo + gradient
function createFallbackBackground(journal, year) {
  const gradient = publisherGradients[journal] || publisherGradients.default;
  return gradient;
}

$(document).ready(function() {
  // Parse publications from table (works on all screen sizes)
  const isMobile = window.innerWidth <= 600;
  const cardsPerView = isMobile ? 1 : 3;
    const publications = [];

    $('.dataframe tbody tr').each(function() {
      const cells = $(this).find('td');
      const titleHtml = cells.eq(1).html();
      const semanticScholarUrl = $(titleHtml).attr('href');

      publications.push({
        paperId: extractPaperId(semanticScholarUrl),
        titleHtml: titleHtml,
        authors: cells.eq(2).text(),
        journal: cells.eq(3).text(),
        citations: parseInt(cells.eq(4).text()),
        year: parseInt(cells.eq(5).text())
      });
    });

    // Generate carousel cards
    publications.forEach((pub, index) => {
      const card = `
        <div class="publication-card" data-card-index="${index}">
          <div class="publication-card-figure loading" data-figure-container="${index}"></div>
          <div class="publication-card-content">
            <div class="publication-card-title">${pub.titleHtml}</div>
            <div class="publication-card-authors">${pub.authors}</div>
            <div class="publication-card-meta">
              <span class="publication-card-journal">${pub.journal}</span>
              <span class="publication-card-year">${pub.year}</span>
              <span class="publication-card-citations">${pub.citations.toLocaleString()} citations</span>
            </div>
          </div>
        </div>
      `;

      $('.publications-carousel-track').append(card);

      // Generate pagination dots
      const dot = `<div class="carousel-dot ${index === 0 ? 'active' : ''}" data-index="${index}"></div>`;
      $('.publications-carousel-dots').append(dot);

      // Fetch figure asynchronously
      if (pub.paperId) {
        fetchPaperFigure(pub.paperId).then(figureUrl => {
          const $figure = $(`.publication-card-figure[data-figure-container="${index}"]`);
          $figure.removeClass('loading');

          if (figureUrl) {
            // Try to load the figure
            const img = new Image();
            img.onload = function() {
              $figure.css('background-image', `url(${figureUrl})`);
            };
            img.onerror = function() {
              // Fallback to gradient if image fails to load
              const gradient = createFallbackBackground(pub.journal, pub.year);
              $figure.addClass('fallback').css('background', gradient);
            };
            img.src = figureUrl;
          } else {
            // No figure available, use fallback
            const gradient = createFallbackBackground(pub.journal, pub.year);
            $figure.addClass('fallback').css('background', gradient);
          }
        });
      } else {
        // No paper ID, use fallback immediately
        const $figure = $(`.publication-card-figure[data-figure-container="${index}"]`);
        $figure.removeClass('loading');
        const gradient = createFallbackBackground(pub.journal, pub.year);
        $figure.addClass('fallback').css('background', gradient);
      }
    });

    // Carousel navigation
    let currentIndex = 0;
    const totalCards = publications.length;
    const maxIndex = Math.ceil(totalCards / cardsPerView) - 1;

    function updateCarousel() {
      let offset;
      if (isMobile) {
        offset = -currentIndex * 100;
      } else {
        // Desktop: calculate offset based on card width + gap
        const cardWidth = 33.333; // percentage
        const gapPercentage = (24 / $('.publications-carousel-container').width()) * 100;
        offset = -currentIndex * cardsPerView * (cardWidth + gapPercentage);
      }

      $('.publications-carousel-track').css('transform', `translateX(${offset}%)`);

      // Update dots
      $('.carousel-dot').removeClass('active');
      if (isMobile) {
        $(`.carousel-dot[data-index="${currentIndex}"]`).addClass('active');
      } else {
        // Highlight all visible cards' dots on desktop
        for (let i = 0; i < cardsPerView; i++) {
          const dotIndex = currentIndex * cardsPerView + i;
          if (dotIndex < totalCards) {
            $(`.carousel-dot[data-index="${dotIndex}"]`).addClass('active');
          }
        }
      }
    }

    function goToSlide(index) {
      currentIndex = Math.max(0, Math.min(index, maxIndex));
      updateCarousel();
    }

    // Arrow navigation
    $('.carousel-prev').on('click', function() {
      goToSlide(currentIndex - 1);
    });

    $('.carousel-next').on('click', function() {
      goToSlide(currentIndex + 1);
    });

    // Dot navigation
    $('.publications-carousel-dots').on('click', '.carousel-dot', function() {
      const dotIndex = parseInt($(this).data('index'));
      if (isMobile) {
        goToSlide(dotIndex);
      } else {
        // Desktop: calculate which page contains this card
        const pageIndex = Math.floor(dotIndex / cardsPerView);
        goToSlide(pageIndex);
      }
    });

    // Touch/swipe support
    let touchStartX = 0;
    let touchEndX = 0;

    $('.publications-carousel-track').on('touchstart', function(e) {
      touchStartX = e.changedTouches[0].screenX;
    });

    $('.publications-carousel-track').on('touchend', function(e) {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    });

    function handleSwipe() {
      const swipeThreshold = 50;
      const diff = touchStartX - touchEndX;

      if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
          // Swipe left - next
          goToSlide(currentIndex + 1);
        } else {
          // Swipe right - previous
          goToSlide(currentIndex - 1);
        }
      }
    }

    // Keyboard navigation
    $(document).on('keydown', function(e) {
      if ($('.publications-carousel:visible').length > 0) {
        if (e.key === 'ArrowLeft') {
          goToSlide(currentIndex - 1);
        } else if (e.key === 'ArrowRight') {
          goToSlide(currentIndex + 1);
        }
      }
    });
});
</script>
```

**How it works:**
1. Parse publication data from existing table
2. Generate carousel with responsive card count:
   - **Desktop (>600px):** 3 cards visible, advance by 3
   - **Mobile (≤600px):** 1 card visible, advance by 1
3. Extract Semantic Scholar paper IDs from URLs
4. Query Semantic Scholar API for external IDs (PMID, PMCID)
5. If PMID/PMCID available, attempt to fetch figure from Europe PMC
6. If figure found, display it; otherwise fall back to publisher-branded gradient
7. Show loading shimmer while fetching
8. Add navigation: arrows, dots, swipe gestures, keyboard

**Benefits:**
- Real paper figures where available (professional, content-representative)
- Graceful degradation to branded gradients
- Responsive design: 3 cards on desktop, 1 on mobile
- Multiple navigation methods (arrows, dots, swipe, keyboard)
- Asynchronous loading doesn't block card rendering
- Uses existing table as single source of truth
- No manual curation required
- Replaces DataTable with more visual, engaging experience

### 4. Optional: Add Simple Search for Cards

If search is needed on mobile, add a search input and filter logic in Publications.html:

```html
<div class="publications-mobile-search" style="display: none;">
  <input type="text" id="mobile-pub-search" placeholder="Search publications...">
</div>

<script>
$(document).ready(function() {
  if (window.innerWidth <= 600) {
    $('.publications-mobile-search').show();

    $('#mobile-pub-search').on('input', function() {
      const query = $(this).val().toLowerCase();
      $('.publication-card').each(function() {
        const text = $(this).text().toLowerCase();
        $(this).toggle(text.includes(query));
      });
    });
  }
});
</script>
```

## Critical Files to Modify

1. [_sass/_custom.scss](_sass/_custom.scss) - Add mobile card styles, hide DataTables on mobile
2. [_includes/Publications.html](_includes/Publications.html) - Add card HTML structure
3. [_includes/publications.md](_includes/publications.md) - May need to convert to YAML data file for templating

## Verification Steps

1. **Desktop (>600px):**
   - Verify carousel displays 3 cards at once
   - Test arrow navigation (advances by 3 cards)
   - Test dot navigation (jumps to correct page)
   - Test keyboard arrows (left/right navigation)
   - Verify card hover effects work
   - Check figures load or fall back to gradients appropriately
   - Confirm spacing between cards is consistent

2. **Tablet (600px):**
   - Verify smooth transition from 3-card to 1-card layout
   - Check card width adjusts properly
   - Test touch/swipe gestures work
   - Confirm no horizontal overflow

3. **Mobile (375px - iPhone SE):**
   - Verify carousel displays 1 card at a time
   - Test swipe left/right navigation
   - Test arrow button touch targets (minimum 44px)
   - Verify card content is readable (proper font sizes)
   - Test dot navigation (jumps to specific card)
   - Check figure aspect ratio (280px → 240px on <400px)
   - Test on actual device for smooth swipe gestures
   - Verify momentum scrolling works on iOS

4. **Figure Loading:**
   - Verify loading shimmer displays while fetching
   - Test Europe PMC API integration for papers with PMID/PMCID
   - Confirm fallback gradients display for papers without figures
   - Check different publisher gradients (Nature, Biorxiv, arXiv, etc.)
   - Verify image error handling (falls back to gradient)

5. **Accessibility:**
   - Test keyboard navigation (left/right arrows)
   - Tab through navigation buttons
   - Test with screen reader (ARIA labels on buttons)
   - Verify color contrast meets WCAG AA standards
   - Check focus indicators are visible on dots and buttons
   - Ensure carousel is navigable without mouse

6. **Cross-browser:**
   - Test on Safari iOS, Chrome Android, Firefox, Edge
   - Verify -webkit-line-clamp works (author truncation)
   - Check CSS custom properties render correctly
   - Test touch gestures on various mobile devices
   - Verify CSS flexbox gap support (fallback if needed)
   - Check gradient rendering consistency

7. **Performance:**
   - Verify carousel animates smoothly (60fps)
   - Check that asynchronous figure loading doesn't block UI
   - Test with slow network (loading states visible)
   - Ensure no layout shift when figures load

## Research Sources

Information about paper figure APIs was researched from:
- [Semantic Scholar Academic Graph API](https://www.semanticscholar.org/product/api)
- [Semantic Scholar API Documentation](https://api.semanticscholar.org/api-docs/)
- [Europe PMC API Documentation](https://europepmc.org/help)
- [PubMed Central OA Web Service API](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/)
