/* Global variables */
let mainNavHeight: number;
let siblings: {
  p: { index: number; target: string };
  n: { index: number; target: string };
} | null;
let targets: {
  c: { target: string; index: number };
  s: { p: { index: number; target: string }; n: { index: number; target: string } } | null;
} | null;
let scrollPosition: number = 0;

function disable_scroll(): void {
  // Save current scroll position
  scrollPosition = window.scrollY;

  const body = document.body;
  body.style.position = 'fixed';
  body.style.top = `-${scrollPosition}px`;
  body.style.width = '100%';
  body.classList.add('stop-scrolling');
  body.addEventListener('touchmove', (e) => e.preventDefault(), { passive: false });
}

function enable_scroll(): void {
  const body = document.body;
  body.classList.remove('stop-scrolling');
  body.style.position = '';
  body.style.top = '';
  body.style.width = '';
  body.removeEventListener('touchmove', (e) => e.preventDefault());

  // Restore scroll position
  window.scrollTo(0, scrollPosition);
}

function loadCV(): void {
  // Remove any existing modals manually (bootbox.hideAll() has compatibility issues)
  document.querySelectorAll('.bootbox, .modal-backdrop').forEach((el) => el.remove());

  // Check if we need to scroll to About section first
  const aboutEl = document.getElementById('About');
  if (!aboutEl) return;

  const aboutTop = aboutEl.getBoundingClientRect().top + window.scrollY - mainNavHeight;
  const currentScroll = window.scrollY;

  function openCVModal(): void {
    disable_scroll();

    const cvContent = document.getElementById('cv-content');
    if (!cvContent) return;

    bootbox.dialog({
      message: cvContent.innerHTML,
      onEscape: true,
      backdrop: true,
    });

    const bootboxEl = document.querySelector('.bootbox');
    if (!bootboxEl) return;

    bootboxEl.classList.add('cv-modal');

    // Style the download button positioning within modal
    const modalBody = document.querySelector<HTMLElement>('.bootbox .modal-body');
    if (modalBody) modalBody.style.position = 'relative';

    const downloadBtn = document.querySelector<HTMLElement>('.bootbox #cv-download-btn');
    if (downloadBtn) {
      Object.assign(downloadBtn.style, {
        position: 'absolute',
        top: '45px',
        right: '50px',
        zIndex: '100',
      });
    }

    // Calculate even spacing: 20px from navbar bottom and 20px from viewport bottom
    const spacing = 20;
    const topOffset = mainNavHeight + spacing;
    const availableHeight = window.innerHeight - topOffset - spacing;

    // Style the outer modal container for proper positioning
    (bootboxEl as HTMLElement).style.overflow = 'hidden';

    // Style the modal dialog with fixed positioning for precise control
    const modalDialog = document.querySelector<HTMLElement>('.bootbox .modal-dialog');
    if (modalDialog) {
      Object.assign(modalDialog.style, {
        position: 'fixed',
        top: `${topOffset}px`,
        left: '50%',
        transform: 'translateX(-50%)',
        backgroundColor: '#fff',
        border: 'none',
        borderRadius: '8px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.3)',
        width: '80%',
        maxWidth: '900px',
        height: `${availableHeight}px`,
        maxHeight: `${availableHeight}px`,
        overflowY: 'auto',
        margin: '0',
      });
    }

    // Ensure modal content fills the dialog
    const modalContent = document.querySelector<HTMLElement>('.bootbox .modal-content');
    if (modalContent) {
      Object.assign(modalContent.style, {
        border: 'none',
        boxShadow: 'none',
        width: '100%',
      });
    }

    // Style the close button
    const closeBtn = document.querySelector<HTMLElement>('.bootbox .bootbox-close-button');
    if (closeBtn) {
      Object.assign(closeBtn.style, {
        color: '#333',
        opacity: '0.6',
        fontSize: '24px',
        padding: '10px',
        position: 'absolute',
        right: '15px',
        top: '10px',
        zIndex: '10',
      });
    }

    document.querySelector<HTMLButtonElement>('button.bootbox-close-button.close')?.addEventListener('click', enable_scroll);
    document.querySelector<HTMLDivElement>('div.modal-backdrop')?.addEventListener('click', () => {
      document.querySelectorAll('.bootbox, .modal-backdrop').forEach((el) => el.remove());
      enable_scroll();
    });
  }

  // If not scrolled past the About section, scroll there first
  if (currentScroll < aboutTop) {
    smoothScrollTo(aboutTop, 400);
    setTimeout(openCVModal, 450);
  } else {
    openCVModal();
  }
}

/* bootstrap accordion class active */
function accordionActive(): void {
  jQuery('.accordion')
    .on('show', function (e: JQuery.TriggeredEvent) {
      jQuery(e.target).prev('.accordion-heading').find('.accordion-toggle').addClass('active');
    })
    .on('hide', function (e: JQuery.TriggeredEvent) {
      jQuery(this).find('.accordion-toggle').not(jQuery(e.target)).removeClass('active');
    })
    .each(function () {
      const $a = jQuery(this);
      $a.find('a.accordion-toggle').attr('data-parent', '#' + $a.attr('id'));
    });
}

/* helper : scroll function */
function smoothScrollTo(targetTop: number, duration: number = 600): void {
  // Try native smooth scroll first
  try {
    window.scrollTo({
      top: targetTop,
      behavior: 'smooth',
    });
  } catch (e) {
    // Fallback to jQuery animate for older browsers
    $('html, body').animate({ scrollTop: targetTop }, duration);
  }
}

function scrollToAnchor(aid: JQuery): void {
  const targetTop = (aid.offset()?.top ?? 0) - mainNavHeight;
  smoothScrollTo(targetTop);
}

/* prevent default browser behaviour when there is # in url */
setTimeout(() => {
  if (location.hash) {
    window.scrollTo(0, 0);
  }
}, 1);

document.addEventListener('DOMContentLoaded', () => {
  const mainNav = document.getElementById('MainNav');
  if (mainNav) {
    mainNavHeight = mainNav.offsetHeight;
  }
  accordionActive();

  /* Custom mobile nav toggle */
  const navToggle = document.querySelector<HTMLElement>('#MainNav .btn-navbar');
  if (navToggle) {
    navToggle.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const navCollapse = document.querySelector<HTMLElement>('#MainNav .nav-collapse');
      if (navCollapse) {
        navCollapse.classList.toggle('in');
      }
      navToggle.classList.toggle('collapsed');
    });
  }
});

window.addEventListener('load', () => {
  /* easy pie chart */
  jQuery('.pie-chart').each(function () {
    const $t = jQuery(this);
    const scaleColor = $t.attr('data-scalecolor');
    const trackColor = $t.attr('data-trackcolor');

    $t.easyPieChart({
      animate: $t.attr('data-animate'),
      barColor: $t.attr('data-barcolor'),
      trackColor: trackColor,
      scaleColor: scaleColor === 'false' ? false : scaleColor,
      lineCap: $t.attr('data-linecap'),
      lineWidth: $t.attr('data-linewidth'),
      size: $t.attr('data-size'),
    });
  });

  /* flexslider */
  $('.work .flexslider').flexslider({ slideshow: false });
  $('.work .flexslider .slides li:first-child').addClass('flex-active-slide').css({ display: 'list-item' });
  $('#BlogBody .post-media.flexslider').flexslider({ slideshow: false, controlNav: false });

  /* main navigation scrolling */
  const $nav = $('#MainNav.sticky');
  const mainHeader = document.getElementById('MainHeader');
  const mainHeaderHeight = mainHeader ? mainHeader.offsetHeight : 0;

  function updateNavbarVisibility(): void {
    const scrollTop = window.scrollY;
    if (scrollTop > mainHeaderHeight - 100) {
      $nav.removeClass('navbar-hidden').addClass('stick');
    } else {
      $nav.addClass('navbar-hidden').removeClass('stick');
    }
  }

  updateNavbarVisibility();
  window.addEventListener('scroll', updateNavbarVisibility);

  $('#MainNav a[href^="#"]').on('click', function (e) {
    const navBtn = document.querySelector<HTMLButtonElement>('#MainNav button');
    if (navBtn && !navBtn.classList.contains('collapsed')) {
      navBtn.click();
    }

    e.preventDefault();
    const target = (this as HTMLAnchorElement).hash;
    const $target = $(target);
    let offset: number;

    if (target === '#MainNav') {
      offset = $target.offset()?.top ?? 0;
    } else if (document.documentElement.clientWidth <= 980) {
      offset = $target.offset()?.top ?? 0;
    } else {
      offset = ($target.offset()?.top ?? 0) - mainNavHeight;
    }
    smoothScrollTo(offset);
  });

  /* After everything is loaded, scroll to hash */
  setTimeout(() => {
    if (location.hash) {
      const $navElem = $('#MainNav.sticky');
      const navPosition = $navElem.css('position');
      const hashOffset = $(location.hash).offset()?.top ?? 0;
      const scrollOffset = navPosition === 'fixed' ? hashOffset - mainNavHeight : hashOffset;
      window.scrollTo(0, scrollOffset);
    }
  }, 150);

  $('.post-meta .comment a[href^="#"]').on('click', function (e) {
    e.preventDefault();
    const $target = $((this as HTMLAnchorElement).hash);
    const offset =
      document.documentElement.clientWidth <= 980
        ? $target.offset()?.top ?? 0
        : ($target.offset()?.top ?? 0) - mainNavHeight;
    smoothScrollTo(offset);
  });

  /* works ajax portfolio */
  const workThumbnails = $('.work .preview ul.slides li a');

  workThumbnails.each(function (index) {
    $(this).data('index', index + 1);
  });

  function showFullView(): void {
    $('.work').removeClass('general').addClass('details');
  }

  function hideFullView(): void {
    $('.work').removeClass('details').addClass('general');
  }

  hideFullView();

  function findSiblings(
    index: number,
    list: JQuery
  ): { p: { index: number; target: string }; n: { index: number; target: string } } {
    let pindex = index - 1;
    let ptarget: string;

    if (pindex <= 0) {
      pindex = list.length;
      ptarget = list.last().attr('href') ?? '';
    } else {
      ptarget =
        list
          .filter(function () {
            return $(this).data('index') === pindex;
          })
          .attr('href') ?? '';
    }

    let nindex = index + 1;
    let ntarget: string;

    if (nindex > workThumbnails.length) {
      nindex = 1;
      ntarget = list.first().attr('href') ?? '';
    } else {
      ntarget =
        list
          .filter(function () {
            return $(this).data('index') === nindex;
          })
          .attr('href') ?? '';
    }

    return {
      p: { index: pindex, target: ptarget },
      n: { index: nindex, target: ntarget },
    };
  }

  const container = $('.work > .container');
  const box = $('section.full-view', container);

  /* Load content with Ajax when thumbnail is clicked */
  $('.work .preview .slides a').on('click', function (e) {
    e.preventDefault();
    const $work = $('.work');
    targets = {
      c: {
        target: $(this).attr('href') ?? '',
        index: $(this).data('index') as number,
      },
      s: null,
    };
    targets.s = findSiblings(targets.c.index, workThumbnails);

    if (targets.c.target !== '#' && targets.c.target !== '') {
      $('.work .full-view').load(targets.c.target, function () {
        const currentTarget = targets?.c.target ?? '';
        const currentIndex = targets?.c.index ?? 0;
        $('.work').data('target', currentTarget).data('index', currentIndex);

        showFullView();

        /* create sibling box elements for next/prev navigation */
        box
          .clone()
          .removeClass()
          .addClass('full-view row-fluid left clone')
          .appendTo(container)
          .load(targets?.s?.p.target ?? '');
        box
          .clone()
          .removeClass()
          .addClass('full-view row-fluid right clone')
          .appendTo(container)
          .load(targets?.s?.n.target ?? '');
        box.addClass('original');
      });
    }
    scrollToAnchor($work);
  });

  function slide(dir: 'l' | 'r'): void {
    const $work = $('.work');
    $('.full-view', $work).removeClass('invisible');
    let rclone = $('.clone.right', $work);
    let lclone = $('.clone.left', $work);
    const original = $('.original', $work);

    if (dir === 'l') {
      const nTarget = siblings?.n.target ?? '';
      const nIndex = findSiblings($work.data('index') as number, workThumbnails).n.index;
      $work.data('target', nTarget).data('index', nIndex);
      siblings = findSiblings($work.data('index') as number, workThumbnails);

      rclone.toggleClass('clone right original');
      original.toggleClass('clone original left');
      lclone.toggleClass('left right invisible');
      rclone = $('.clone.right', $work);
      rclone.load(siblings?.n.target ?? '');
    } else if (dir === 'r') {
      const pTarget = siblings?.p.target ?? '';
      const pIndex = findSiblings($work.data('index') as number, workThumbnails).p.index;
      $work.data('target', pTarget).data('index', pIndex);
      siblings = findSiblings($work.data('index') as number, workThumbnails);

      lclone.toggleClass('clone left original');
      original.toggleClass('clone original right');
      rclone.toggleClass('right left invisible');
      lclone = $('.clone.left', $work);
      lclone.load(siblings?.p.target ?? '');
    }
  }

  $(document).on('click', '.work .full-view nav a.all', function () {
    hideFullView();
    $('.work .clone').remove();
    return false;
  });

  $(document).on('click', '.work .full-view nav a.prev', function () {
    slide('r');
    return false;
  });

  $(document).on('click', '.work .full-view nav a.next', function () {
    slide('l');
    return false;
  });

  /* mail validation */
  $("input[type='email']").on('blur', function () {
    $(this).toggleClass('filled', !!$(this).val());
  });
});

// Export loadCV to global scope so it can be called from HTML onclick
(window as any).loadCV = loadCV;

// Export to make this a module
export {};
