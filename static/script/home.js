document.addEventListener('DOMContentLoaded', () => {

    // ==================================================
    // HELPER FUNCTIONS
    // ==================================================
    function buildWatchUrl(animeId) {
        return `/watch/${animeId}/`;
    }

    // ==================================================
    // PRELOADER: hanya muncul kalau dari login (?from=login)
    // ==================================================
    const preloader = document.getElementById('preloader');
    const progressBar = document.getElementById('loader-progress');
    const loadingText = document.getElementById('loadingText');

    const params = new URLSearchParams(window.location.search);
    const fromLogin = params.get('from') === 'login';

    // Kalau bukan dari login -> preloader tidak muncul sama sekali
    if (!fromLogin) {
        if (preloader) preloader.style.display = 'none';
    } else {
        // OPTIONAL: hapus query param biar refresh tidak muncul lagi
        try {
            window.history.replaceState({}, document.title, window.location.pathname);
        } catch (_) {}

        // =========================
        // PRELOADER JALAN DI SINI
        // =========================
        const loadingMessages = [
            'Initializing Core Systems...',
            'Loading your recommendations...',
            'Fetching latest episodes...',
            'Preparing your watch list...',
            'Almost ready!'
        ];

        let messageIndex = 0;
        let progress = 0;

        const updateLoadingMessage = () => {
            if (loadingText && messageIndex < loadingMessages.length) {
                loadingText.textContent = loadingMessages[messageIndex];
                messageIndex++;
            }
        };

        updateLoadingMessage();

        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 100) progress = 100;

            if (progressBar) progressBar.style.width = `${progress}%`;

            if (progress > 20 && messageIndex === 1) updateLoadingMessage();
            if (progress > 40 && messageIndex === 2) updateLoadingMessage();
            if (progress > 60 && messageIndex === 3) updateLoadingMessage();
            if (progress > 80 && messageIndex === 4) updateLoadingMessage();

            if (progress === 100) {
                clearInterval(interval);
                setTimeout(() => {
                    if (!preloader) return;
                    preloader.style.opacity = '0';
                    setTimeout(() => {
                        preloader.style.display = 'none';
                        animateHeroText(); // tetap panggil animasi setelah preloader selesai
                    }, 800);
                }, 500);
            }
        }, 150);
    }


    // ==================================================
    // 2. HERO CAROUSEL WITH ADD TO LIST FUNCTIONALITY
    // ==================================================
    const slider = {
        slides: document.querySelectorAll('.hero-slide'),
        dotsContainer: document.getElementById('sliderDots'),
        prevBtn: document.getElementById('sliderPrev'),
        nextBtn: document.getElementById('sliderNext'),
        bgContainer: document.getElementById('heroBgContainer'),
        currentIndex: 0,
        timer: null,

        init() {
            if (!this.slides || this.slides.length === 0) return;

            this.slides.forEach((_, index) => {
                const dot = document.createElement('div');
                dot.classList.add('dot');
                if (index === 0) dot.classList.add('active');
                dot.addEventListener('click', () => this.goToSlide(index));
                if (this.dotsContainer) this.dotsContainer.appendChild(dot);
            });

            if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.prevSlide());
            if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.nextSlide());

            // Add to list button functionality for carousel
            this.initAddToListButtons();

            this.startAutoPlay();
            this.updateBackground();
        },

        initAddToListButtons() {
            const addToListBtns = document.querySelectorAll('.btn-add-list');

            addToListBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const slide = btn.closest('.hero-slide');
                    const animeTitle = slide ? slide.getAttribute('data-anime') : '';

                    if (!btn.classList.contains('added')) {
                        btn.classList.add('added');
                        const icon = btn.querySelector('i');
                        if (icon) {
                            icon.classList.remove('fa-plus');
                            icon.classList.add('fa-check');
                        }
                        showNotification(`"${animeTitle}" has been added to your list`);
                    } else {
                        btn.classList.remove('added');
                        const icon = btn.querySelector('i');
                        if (icon) {
                            icon.classList.remove('fa-check');
                            icon.classList.add('fa-plus');
                        }
                        showNotification(`"${animeTitle}" has been removed from your list`);
                    }
                });
            });
        },

        updateBackground() {
            const currentSlide = this.slides[this.currentIndex];
            if (!currentSlide || !this.bgContainer) return;

            const bgFile = currentSlide.getAttribute('data-bg');
            if (bgFile) {
                this.bgContainer.style.backgroundImage = `url('${bgFile}')`;
            }
        },

        updateClasses() {
            this.slides.forEach(slide => slide.classList.remove('active'));
            if (this.slides[this.currentIndex]) this.slides[this.currentIndex].classList.add('active');

            const dots = document.querySelectorAll('.dot');
            dots.forEach(dot => dot.classList.remove('active'));
            if (dots[this.currentIndex]) dots[this.currentIndex].classList.add('active');

            const info = this.slides[this.currentIndex]?.querySelectorAll('.fade-up') || [];
            info.forEach(el => {
                el.style.animation = 'none';
                el.offsetHeight;
                el.style.animation = null;
            });

            this.updateBackground();
        },

        goToSlide(index) {
            this.currentIndex = index;
            if (this.currentIndex >= this.slides.length) this.currentIndex = 0;
            if (this.currentIndex < 0) this.currentIndex = this.slides.length - 1;
            this.updateClasses();
            this.resetTimer();
        },

        nextSlide() {
            this.goToSlide(this.currentIndex + 1);
        },

        prevSlide() {
            this.goToSlide(this.currentIndex - 1);
        },

        startAutoPlay() {
            this.timer = setInterval(() => this.nextSlide(), 6000);
        },

        resetTimer() {
            clearInterval(this.timer);
            this.startAutoPlay();
        }
    };

    slider.init();


    // ==================================================
    // 3. SCROLL EFFECTS
    // ==================================================
    const header = document.getElementById('mainHeader');
    const backToTop = document.getElementById('backToTop');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            if (header) header.classList.add('scrolled');
            if (backToTop) backToTop.classList.add('show');
        } else {
            if (header) header.classList.remove('scrolled');
            if (backToTop) backToTop.classList.remove('show');
        }
    });

    const revealElements = document.querySelectorAll('.scroll-reveal');

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.15
    });

    revealElements.forEach(el => revealObserver.observe(el));


    // ==================================================
    // 4. UI INTERACTIONS
    // ==================================================
    const searchTrigger = document.getElementById('searchTrigger');
    const searchOverlay = document.getElementById('searchOverlay');
    const searchClose = document.getElementById('searchClose');

    if (searchTrigger && searchOverlay) {
        searchTrigger.addEventListener('click', () => {
            searchOverlay.classList.add('active');
        });
    }

    if (searchClose && searchOverlay) {
        searchClose.addEventListener('click', () => {
            searchOverlay.classList.remove('active');
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === "Escape" && searchOverlay && searchOverlay.classList.contains('active')) {
            searchOverlay.classList.remove('active');
        }
    });

    // ==================================================
    // SEARCH OVERLAY REDIRECT TO SEARCH PAGE
    // ==================================================
    const searchInput = searchOverlay?.querySelector('input[type="text"]');
    const searchBtn = searchOverlay?.querySelector('button[type="submit"]');

    function goSearch() {
        const q = (searchInput?.value || "").trim();
        window.location.href = q ? `/search/?q=${encodeURIComponent(q)}` : `/search/`;
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            goSearch();
        });
    }

    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                goSearch();
            }
        });
    }

    const mobileToggle = document.getElementById('mobileToggle');
    const navbar = document.getElementById('navbar');

    if (mobileToggle && navbar) {
        mobileToggle.addEventListener('click', () => {
            navbar.classList.toggle('active');
            const spans = mobileToggle.querySelectorAll('span');
            if (navbar.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }


    // ==================================================
    // 5. USER PROFILE DROPDOWN
    // ==================================================
    const userBtn = document.getElementById('userBtn');
    const userDropdown = document.getElementById('userDropdown');

    if (userBtn && userDropdown) {
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('active');
        });

        document.addEventListener('click', function(e) {
            if (!userBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                userDropdown.classList.remove('active');
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && userDropdown.classList.contains('active')) {
                userDropdown.classList.remove('active');
            }
        });
    }


    // ==================================================
    // 6. ANIME CARD INTERACTIONS WITH + ICON
    // ==================================================
    const animeCards = document.querySelectorAll('.anime-card');

    animeCards.forEach(card => {
        const cardLink = card.querySelector('.card-link');
        const listBtn = card.querySelector('.list-btn');
        const favoriteBtn = card.querySelector('.favorite-btn');

        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });

        card.addEventListener('click', function(e) {
            if (!e.target.closest('.card-link') && !e.target.closest('.action-icon-btn') && cardLink) {
                cardLink.click();
            }
        });

        if (listBtn) {
            listBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.toggle('active');

                const animeTitleEl = card.querySelector('.anime-title');
                const animeTitle = animeTitleEl ? animeTitleEl.textContent : '';
                const icon = this.querySelector('i');

                if (this.classList.contains('active')) {
                    if (icon) {
                        icon.classList.remove('fa-plus');
                        icon.classList.add('fa-check');
                    }
                    showNotification(`"${animeTitle}" has been added to your list`);
                } else {
                    if (icon) {
                        icon.classList.remove('fa-check');
                        icon.classList.add('fa-plus');
                    }
                    showNotification(`"${animeTitle}" has been removed from your list`);
                }
            });
        }

        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.toggle('active');

                const animeTitleEl = card.querySelector('.anime-title');
                const animeTitle = animeTitleEl ? animeTitleEl.textContent : '';
                const icon = this.querySelector('i');

                if (this.classList.contains('active')) {
                    if (icon) {
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                    }
                    showNotification(`"${animeTitle}" has been added to favorites`);
                } else {
                    if (icon) {
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                    }
                    showNotification(`"${animeTitle}" has been removed from favorites`);
                }
            });
        }
    });


    // ==================================================
    // 7. TOP VIEWS & TODAY - FETCH FROM API
    // ==================================================
    
    // Fetch Top Views data from API
    async function fetchTopViews(timeframe = "day") {
        try {
            const res = await fetch(`/api/widgets/top-views/?timeframe=${timeframe}`, { 
                credentials: "same-origin" 
            });
            const json = await res.json();
            if (json.status === "success") return json.data || [];
        } catch (e) {
            console.error("Error fetching top views:", e);
        }
        return [];
    }

    // Fetch Today episodes data from API
    async function fetchToday() {
        try {
            const res = await fetch(`/api/widgets/today/`, { 
                credentials: "same-origin" 
            });
            const json = await res.json();
            if (json.status === "success") return json.data || [];
        } catch (e) {
            console.error("Error fetching today episodes:", e);
        }
        return [];
    }


    // ==================================================
    // 8. WIDGET PAGINATION WITH SMOOTH TRANSITIONS
    // ==================================================
    class WidgetPagination {
        constructor(data, contentId, prevBtnId, nextBtnId, itemsPerPage = 5, renderFunction, hasRank = true) {
            this.data = data;
            this.contentElement = document.getElementById(contentId);
            this.prevBtn = document.getElementById(prevBtnId);
            this.nextBtn = document.getElementById(nextBtnId);
            this.itemsPerPage = itemsPerPage;
            this.currentPage = 0;
            this.renderFunction = renderFunction;
            this.hasRank = hasRank;

            this.init();
        }

        init() {
            this.render();
            this.updateButtons();

            if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.prevPage());
            if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.nextPage());
        }

        render(animate = false) {
            if (!this.contentElement) return;

            if (animate) {
                this.contentElement.classList.add('transitioning');
            }

            setTimeout(() => {
                const startIndex = this.currentPage * this.itemsPerPage;
                const endIndex = startIndex + this.itemsPerPage;
                const pageData = this.data.slice(startIndex, endIndex);

                this.contentElement.innerHTML = '';
                pageData.forEach((item, index) => {
                    const rank = startIndex + index + 1;
                    this.contentElement.appendChild(this.renderFunction(item, rank, this.hasRank));
                });

                if (animate) {
                    this.contentElement.classList.remove('transitioning');
                }
            }, animate ? 200 : 0);
        }

        updateButtons() {
            if (!this.prevBtn || !this.nextBtn) return;

            const totalPages = Math.ceil(this.data.length / this.itemsPerPage);
            this.prevBtn.disabled = this.currentPage === 0;
            this.nextBtn.disabled = this.currentPage >= totalPages - 1;
        }

        nextPage() {
            const totalPages = Math.ceil(this.data.length / this.itemsPerPage);
            if (this.currentPage < totalPages - 1) {
                this.currentPage++;
                this.render(true);
                this.updateButtons();
            }
        }

        prevPage() {
            if (this.currentPage > 0) {
                this.currentPage--;
                this.render(true);
                this.updateButtons();
            }
        }

        setData(newData) {
            this.data = newData;
            this.currentPage = 0;
            this.render(true);
            this.updateButtons();
        }
    }

    function renderTopViewItem(item, rank, hasRank = true) {
        const div = document.createElement('div');
        div.className = 'sidebar-item' + (hasRank ? ' with-rank' : '');
        if (hasRank) div.setAttribute('data-rank', rank);

        const watchUrl = item.anime_id ? buildWatchUrl(item.anime_id) : "#";

        div.innerHTML = `
            <div class="item-img">
                <img src="${item.image}" alt="${item.title}">
            </div>
            <div class="item-info">
                <h5><a href="${watchUrl}">${item.title}</a></h5>
                <span class="views"><i class="fas fa-eye"></i> ${Number(item.views || 0).toLocaleString()}</span>
            </div>
        `;
        return div;
    }

    function renderTodayItem(item) {
        const div = document.createElement('div');
        div.className = 'sidebar-item';

        const watchUrl = item.anime_id ? buildWatchUrl(item.anime_id) : "#";

        div.innerHTML = `
            <div class="item-img">
                <img src="${item.image}" alt="${item.title}">
            </div>
            <div class="item-info">
                <h5><a href="${watchUrl}">${item.title}</a></h5>
                <span class="episode">${item.episode}</span>
                <span class="time-badge"><i class="fas fa-clock"></i> ${item.time}</span>
            </div>
        `;
        return div;
    }

    // Initialize pagination with empty data first
    let topViewsPagination = new WidgetPagination(
        [],
        'topViewsContent',
        'topViewsPrev',
        'topViewsNext',
        5,
        renderTopViewItem,
        true
    );

    const todayPagination = new WidgetPagination(
        [],
        'todayContent',
        'todayPrev',
        'todayNext',
        5,
        renderTodayItem,
        false
    );

    // Load initial data from API
    (async () => {
        const dayData = await fetchTopViews("day");
        topViewsPagination.setData(dayData);

        const today = await fetchToday();
        todayPagination.setData(today);
    })();

    // Widget navigation (Day/Week/Month) for Top Views
    const widgetNavItems = document.querySelectorAll('.widget-nav span');

    widgetNavItems.forEach(item => {
        item.addEventListener('click', async function() {
            widgetNavItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const timeframe = this.getAttribute('data-timeframe');
            const newData = await fetchTopViews(timeframe);
            topViewsPagination.setData(newData);
        });
    });


    // ==================================================
    // 9. BACK TO TOP BUTTON
    // ==================================================
    if (backToTop) {
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }


    // ==================================================
    // 10. UTILS
    // ==================================================
    function animateHeroText() {
        const activeSlide = document.querySelector('.hero-slide.active');
        if (activeSlide) {
            const elements = activeSlide.querySelectorAll('.fade-up');
            elements.forEach(el => {
                el.style.animationPlayState = 'running';
            });
        }
    }

    function showNotification(message) {
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) existingNotification.remove();

        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        `;
        notification.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: var(--bg-card);
            color: var(--text-white);
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 10px 30px var(--shadow-heavy);
            border-left: 4px solid var(--accent);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            max-width: 350px;
        `;

        const icon = notification.querySelector('i');
        icon.style.cssText = `
            color: var(--accent);
            font-size: 18px;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }


    // ==================================================
    // 11. PERFORMANCE OPTIMIZATIONS
    // ==================================================
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    const optimizedScrollHandler = debounce(() => {
        // Scroll effects logic here (optional)
    }, 10);

    window.addEventListener('scroll', optimizedScrollHandler);


    // ==================================================
    // 12. ACCESSIBILITY IMPROVEMENTS
    // ==================================================
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') slider.prevSlide();
        else if (e.key === 'ArrowRight') slider.nextSlide();
    });

    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        element.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstElement) {
                        e.preventDefault();
                        lastElement.focus();
                    }
                } else {
                    if (document.activeElement === lastElement) {
                        e.preventDefault();
                        firstElement.focus();
                    }
                }
            }
        });
    }

    if (searchOverlay) trapFocus(searchOverlay);

    console.log('AnimeStream initialized successfully!');
    console.log('Features: Dynamic API Widgets, Plus Icon Buttons, Green Active State');
});