document.addEventListener('DOMContentLoaded', () => {
    
    /* ==================================================
       INITIAL DATA FROM TEMPLATE
    ================================================== */
    const root = document.querySelector('.watch-container');
    
    // Fungsi untuk decode string yang di-escape oleh Django
    function decodeDjangoEscapeJS(s) {
        if (!s) return "";
        // cara paling aman: parse sebagai JSON string
        try {
            return JSON.parse('"' + s.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"');
        } catch (_) {
            // fallback minimal untuk kasus umum
            return s.replace(/\\u003B/g, ';');
        }
    }
    
    // Ambil dan decode judul anime
    const rawAnimeTitle = root?.dataset.animeTitle || '';
    const animeTitle = decodeDjangoEscapeJS(rawAnimeTitle);
    
    // Data lainnya
    const animeId = root?.dataset.animeId;
    const coverUrl = root?.dataset.coverUrl || '';
    const initialUserRating = parseFloat(root?.dataset.userRating || '0') || 0;
    const episodeCount = parseInt(root?.dataset.episodeCount || '12', 10) || 12;
    const rateApiUrl = root?.dataset.rateApi || '/api/rate/';
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';

    // ===============================
    // COMMENTS (DB) - AniMEStream
    // ===============================
    const COMMENTS_API = root ? root.getAttribute('data-comments-api') : null;
    const LIKE_PREFIX = root ? root.getAttribute('data-like-api-prefix') : "/api/comments/";

    const commentInput = document.getElementById('commentInput');
    const submitComment = document.getElementById('submitComment');
    const cancelComment = document.getElementById('cancelComment');
    const commentsList = document.getElementById('commentsList');

    function getCSRFToken() {
        // ambil dari cookie csrftoken (Django default)
        const name = "csrftoken";
        const cookies = document.cookie ? document.cookie.split(";") : [];
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + "=")) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return "";
    }

    function escapeHtml(str) {
        return (str || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function avatarColorFromName(name) {
        // konsisten per user (biar warna avatar tidak random tiap refresh)
        const colors = ['#ff6b6b', '#6c5ce7', '#00b894', '#fdcb6e', '#e17055', '#0984e3'];
        let hash = 0;
        for (let i = 0; i < (name || "").length; i++) hash = ((hash << 5) - hash) + name.charCodeAt(i);
        const idx = Math.abs(hash) % colors.length;
        return colors[idx];
    }

    async function fetchComments() {
        if (!COMMENTS_API) return [];
        try {
            const res = await fetch(COMMENTS_API, { credentials: "same-origin" });
            const json = await res.json();
            if (json.status === "success") return json.data || [];
        } catch (e) {
            console.error("fetchComments error:", e);
        }
        return [];
    }

    function renderComments(comments) {
        if (!commentsList) return;
        commentsList.innerHTML = "";

        // update count
        const countEl = document.querySelector('.comments-count');
        if (countEl) countEl.textContent = `${comments.length} Comments`;

        if (comments.length === 0) {
            commentsList.innerHTML = `
                <div style="padding:14px; opacity:.75;">
                    No comments yet. Be the first to comment!
                </div>
            `;
            return;
        }

        comments.forEach(comment => {
            const item = document.createElement("div");
            item.className = "comment-item";

            const bg = avatarColorFromName(comment.author);

            item.innerHTML = `
                <div class="comment-avatar" style="background:${bg}">
                    ${escapeHtml(comment.avatar)}
                </div>
                <div class="comment-content">
                    <div class="comment-header">
                        <span class="comment-author">${escapeHtml(comment.author)}</span>
                        <span class="comment-time">${escapeHtml(comment.time)}</span>
                    </div>
                    <div class="comment-text">${escapeHtml(comment.text)}</div>
                    <div class="comment-actions">
                        <div class="comment-action like-btn ${comment.liked ? 'liked' : ''}" data-id="${comment.id}">
                            <i class="fas fa-thumbs-up"></i>
                            <span class="like-count">${comment.likes}</span>
                        </div>
                        <div class="comment-action reply-btn" data-author="${escapeHtml(comment.author)}">
                            <i class="fas fa-reply"></i>
                            <span>Reply</span>
                        </div>
                    </div>
                </div>
            `;
            commentsList.appendChild(item);
        });

        // bind like
        document.querySelectorAll(".like-btn").forEach(btn => {
            btn.addEventListener("click", async function() {
                const id = this.getAttribute("data-id");
                const likeUrl = `${LIKE_PREFIX}${id}/like/`;

                try {
                    const res = await fetch(likeUrl, {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": getCSRFToken(),
                        },
                        credentials: "same-origin",
                    });
                    const json = await res.json();
                    if (json.status === "success") {
                        this.classList.toggle("liked", json.liked);
                        const count = this.querySelector(".like-count");
                        if (count) count.textContent = json.likes;
                    }
                } catch (e) {
                    console.error("toggleLike error:", e);
                }
            });
        });

        // bind reply
        document.querySelectorAll(".reply-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const author = btn.getAttribute("data-author") || "user";
                if (commentInput) {
                    commentInput.value = `@${author} `;
                    commentInput.focus();
                }
            });
        });
    }

    async function reloadComments() {
        const comments = await fetchComments();
        renderComments(comments);
    }

    // submit comment
    if (submitComment) {
        submitComment.addEventListener("click", async () => {
            const text = (commentInput?.value || "").trim();
            if (!text) return;

            try {
                const form = new FormData();
                form.append("text", text);

                const res = await fetch(COMMENTS_API, {
                    method: "POST",
                    body: form,
                    headers: {
                        "X-CSRFToken": getCSRFToken(),
                    },
                    credentials: "same-origin",
                });

                const json = await res.json();
                if (json.status === "success") {
                    commentInput.value = "";
                    await reloadComments();
                    showNotification("Comment posted successfully!", "success");
                } else {
                    showNotification(json.message || "Failed to post comment", "error");
                }
            } catch (e) {
                console.error("postComment error:", e);
                showNotification("Failed to post comment", "error");
            }
        });
    }

    if (cancelComment) {
        cancelComment.addEventListener("click", () => {
            if (commentInput) commentInput.value = "";
        });
    }

    /* ==================================================
       UTILITY FUNCTIONS
    ================================================== */
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    function showNotification(message, type = 'success') {
        const toast = document.getElementById('notificationToast');
        const messageEl = document.getElementById('notificationMessage');
        
        messageEl.textContent = message;
        toast.className = 'notification-toast ' + type;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // CSRF Token helper untuk Django
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /* ==================================================
       VIDEO PLAYER FUNCTIONALITY
    ================================================== */
    const video = document.getElementById('animeVideo');
    const customControls = document.getElementById('customControls');
    const playBtn = document.getElementById('playBtn');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const progressRangeSlider = document.getElementById('progressRangeSlider');
    const currentTimeEl = document.getElementById('currentTime');
    const durationEl = document.getElementById('duration');
    const volumeBtn = document.getElementById('volumeBtn');
    const volumeRangeSlider = document.getElementById('volumeRangeSlider');
    const rewindBtn = document.getElementById('rewindBtn');
    const forwardBtn = document.getElementById('forwardBtn');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const progressArea = document.getElementById('progressArea');
    const videoWrapper = document.querySelector('.video-wrapper');
    const qualityBtn = document.getElementById('qualityBtn');
    const qualityMenu = document.getElementById('qualityMenu');
    const subtitleBtn = document.getElementById('subtitleBtn');
    const subtitleMenu = document.getElementById('subtitleMenu');
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsMenu = document.getElementById('settingsMenu');
    const playbackSpeed = document.getElementById('playbackSpeed');
    const autoplayToggle = document.getElementById('autoplayToggle');
    
    let controlsTimeout;
    let isDraggingProgress = false;

    // Initialize video player
    function initVideoPlayer() {
        // Remove default controls
        video.removeAttribute('controls');
        
        // Set initial volume
        video.volume = 0.8;
        updateVolumeUI();
        
        // Add event listeners
        video.addEventListener('loadedmetadata', () => {
            durationEl.textContent = formatTime(video.duration);
            progressRangeSlider.max = Math.floor(video.duration);
        });
        
        video.addEventListener('timeupdate', updateProgress);
        video.addEventListener('volumechange', updateVolumeUI);
        video.addEventListener('play', () => updatePlayButtons(true));
        video.addEventListener('pause', () => updatePlayButtons(false));
        video.addEventListener('ended', () => updatePlayButtons(false));
        
        // Play/Pause buttons
        playBtn.addEventListener('click', togglePlayPause);
        playPauseBtn.addEventListener('click', togglePlayPause);
        video.addEventListener('click', togglePlayPause);
        
        // Time controls
        rewindBtn.addEventListener('click', () => {
            video.currentTime = Math.max(0, video.currentTime - 10);
        });
        
        forwardBtn.addEventListener('click', () => {
            video.currentTime = Math.min(video.duration, video.currentTime + 10);
        });
        
        // Volume controls
        volumeBtn.addEventListener('click', toggleMute);
        volumeRangeSlider.addEventListener('input', (e) => {
            const volume = e.target.value / 100;
            video.volume = volume;
            video.muted = volume === 0;
            updateVolumeUI();
        });
        
        // Fullscreen
        fullscreenBtn.addEventListener('click', toggleFullscreen);
        
        // Progress bar
        progressRangeSlider.addEventListener('input', (e) => {
            isDraggingProgress = true;
            const time = e.target.value;
            currentTimeEl.textContent = formatTime(time);
            updateProgressBackground();
        });
        
        progressRangeSlider.addEventListener('change', (e) => {
            video.currentTime = e.target.value;
            isDraggingProgress = false;
        });
        
        // Keyboard controls
        document.addEventListener('keydown', handleKeyPress);
        
        // Auto-hide controls
        videoWrapper.addEventListener('mousemove', showControls);
        videoWrapper.addEventListener('mouseleave', hideControlsDelayed);
        customControls.addEventListener('mouseenter', () => clearTimeout(controlsTimeout));
    }

    function togglePlayPause() {
        if (video.paused || video.ended) {
            video.play();
        } else {
            video.pause();
        }
    }

    function updatePlayButtons(isPlaying) {
        const playIcon = isPlaying ? 'fa-pause' : 'fa-play';
        playBtn.innerHTML = `<i class="fas ${playIcon}"></i>`;
        playPauseBtn.innerHTML = `<i class="fas ${playIcon}"></i>`;
        
        // Add margin for play icon to center it visually
        if (!isPlaying) {
            playBtn.querySelector('i').style.marginLeft = '4px';
        } else {
            playBtn.querySelector('i').style.marginLeft = '0';
        }
    }

    function updateProgress() {
        if (!isDraggingProgress) {
            const currentTime = video.currentTime;
            const duration = video.duration;
            
            if (!isNaN(duration) && duration > 0) {
                progressRangeSlider.value = currentTime;
                currentTimeEl.textContent = formatTime(currentTime);
                updateProgressBackground();
            }
        }
    }
    
    function updateProgressBackground() {
        const value = progressRangeSlider.value;
        const max = progressRangeSlider.max;
        const percentage = (value / max) * 100;
        progressRangeSlider.style.background = `linear-gradient(to right, var(--primary) 0%, var(--primary) ${percentage}%, rgba(255,255,255,0.2) ${percentage}%, rgba(255,255,255,0.2) 100%)`;
    }

    function updateBuffer() {
        if (video.buffered.length > 0) {
            const bufferedEnd = video.buffered.end(video.buffered.length - 1);
            const duration = video.duration;
            const bufferPercent = (bufferedEnd / duration) * 100;
            
            // Note: bufferBar might not be defined in your HTML, you can add it if needed
            // const bufferBar = document.getElementById('bufferBar');
            // if (bufferBar) bufferBar.style.width = `${bufferPercent}%`;
        }
    }

    function updateVolumeUI() {
        const volume = video.volume;
        const isMuted = video.muted || volume === 0;
        
        let volumeIcon = 'fa-volume-up';
        if (isMuted || volume === 0) {
            volumeIcon = 'fa-volume-mute';
        } else if (volume < 0.5) {
            volumeIcon = 'fa-volume-down';
        }
        
        volumeBtn.innerHTML = `<i class="fas ${volumeIcon}"></i>`;
        volumeRangeSlider.value = isMuted ? 0 : volume * 100;
        
        // Update slider gradient
        const percentage = isMuted ? 0 : volume * 100;
        volumeRangeSlider.style.background = `linear-gradient(to right, var(--primary) 0%, var(--primary) ${percentage}%, rgba(255,255,255,0.3) ${percentage}%, rgba(255,255,255,0.3) 100%)`;
    }

    function toggleMute() {
        video.muted = !video.muted;
    }
    
    // Subtitle Menu
    if (subtitleBtn) {
        subtitleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            subtitleMenu.classList.toggle('show');
            if (qualityMenu) qualityMenu.classList.remove('show');
            if (settingsMenu) settingsMenu.classList.remove('show');
        });
        
        // Prevent subtitle menu from closing when clicking inside
        if (subtitleMenu) {
            subtitleMenu.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }

    if (subtitleMenu) {
        document.querySelectorAll('.subtitle-menu .menu-item').forEach(item => {
            item.addEventListener('click', function() {
                const subtitle = this.getAttribute('data-subtitle');
                
                // Update active state
                document.querySelectorAll('.subtitle-menu .menu-item i').forEach(icon => {
                    icon.classList.remove('active');
                });
                this.querySelector('i').classList.add('active');
                
                // Close menu
                subtitleMenu.classList.remove('show');
                
                const subtitleText = subtitle === 'off' ? 'Subtitles turned off' : `Subtitles: ${this.querySelector('span').textContent}`;
                showNotification(subtitleText, 'success');
            });
        });
    }
    
    // Quality Menu
    if (qualityBtn) {
        qualityBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            qualityMenu.classList.toggle('show');
            if (settingsMenu) settingsMenu.classList.remove('show');
            if (subtitleMenu) subtitleMenu.classList.remove('show');
        });
        
        // Prevent quality menu from closing when clicking inside
        if (qualityMenu) {
            qualityMenu.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }

    if (qualityMenu) {
        document.querySelectorAll('.quality-menu .menu-item').forEach(item => {
            item.addEventListener('click', function() {
                const quality = this.getAttribute('data-quality');
                
                // Update active state
                document.querySelectorAll('.quality-menu .menu-item i').forEach(icon => {
                    icon.classList.remove('active');
                });
                this.querySelector('i').classList.add('active');
                
                // Update button text
                const qualityTextEl = document.querySelector('.quality-text');
                if (qualityTextEl) {
                    qualityTextEl.textContent = quality;
                }
                
                // Close menu
                qualityMenu.classList.remove('show');
                
                showNotification(`Quality changed to ${quality}`, 'success');
            });
        });
    }
    
    // Settings Menu
    if (settingsBtn) {
        settingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsMenu.classList.toggle('show');
            if (qualityMenu) qualityMenu.classList.remove('show');
            if (subtitleMenu) subtitleMenu.classList.remove('show');
        });
        
        // Prevent settings menu from closing when clicking inside
        if (settingsMenu) {
            settingsMenu.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }
    
    // Playback Speed
    if (playbackSpeed) {
        playbackSpeed.addEventListener('change', (e) => {
            video.playbackRate = parseFloat(e.target.value);
            const speedText = e.target.value === '1' ? 'Normal' : `${e.target.value}x`;
            showNotification(`Playback speed: ${speedText}`, 'success');
        });
        
        // Prevent closing when clicking on speed select
        playbackSpeed.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    // Autoplay Toggle
    if (autoplayToggle) {
        autoplayToggle.addEventListener('change', (e) => {
            const status = e.target.checked ? 'enabled' : 'disabled';
            showNotification(`Autoplay ${status}`, 'success');
        });
    }
    
    // Close menus when clicking outside
    document.addEventListener('click', () => {
        if (qualityMenu) qualityMenu.classList.remove('show');
        if (settingsMenu) settingsMenu.classList.remove('show');
        if (subtitleMenu) subtitleMenu.classList.remove('show');
    });

    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            if (videoWrapper.requestFullscreen) {
                videoWrapper.requestFullscreen();
            } else if (videoWrapper.webkitRequestFullscreen) {
                videoWrapper.webkitRequestFullscreen();
            } else if (videoWrapper.msRequestFullscreen) {
                videoWrapper.msRequestFullscreen();
            }
            if (fullscreenBtn) {
                fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            if (fullscreenBtn) {
                fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
            }
        }
    }

    function handleKeyPress(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch(e.key) {
            case ' ':
            case 'k':
                e.preventDefault();
                togglePlayPause();
                break;
            case 'f':
                e.preventDefault();
                toggleFullscreen();
                break;
            case 'm':
                e.preventDefault();
                toggleMute();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                video.currentTime = Math.max(0, video.currentTime - 10);
                break;
            case 'ArrowRight':
                e.preventDefault();
                video.currentTime = Math.min(video.duration, video.currentTime + 10);
                break;
            case 'ArrowUp':
                e.preventDefault();
                video.volume = Math.min(1, video.volume + 0.1);
                break;
            case 'ArrowDown':
                e.preventDefault();
                video.volume = Math.max(0, video.volume - 0.1);
                break;
        }
    }

    function showControls() {
        if (customControls) {
            customControls.classList.add('show');
            clearTimeout(controlsTimeout);
            hideControlsDelayed();
        }
    }

    function hideControlsDelayed() {
        clearTimeout(controlsTimeout);
        if (!video.paused) {
            controlsTimeout = setTimeout(() => {
                if (customControls) {
                    customControls.classList.remove('show');
                }
            }, 3000);
        }
    }

    // Initialize video player
    if (video) {
        initVideoPlayer();
    }

    /* ==================================================
       EPISODE LIST MANAGEMENT - UPDATED
    ================================================== */
    const episodeList = document.getElementById('episodeList');
    const seasonSelect = document.getElementById('seasonSelect');

    // ✅ FUNGSI BARU: render episodes langsung dari episodeCount
    function renderEpisodes() {
        if (!episodeList) return;
        episodeList.innerHTML = '';

        const epCount = Math.max(1, Math.min(60, episodeCount));

        for (let i = 1; i <= epCount; i++) {
            const episodeItem = document.createElement('div');
            episodeItem.className = `episode-item ${i === 1 ? 'active' : ''}`;

            episodeItem.innerHTML = `
                <div class="episode-thumb">
                    <img src="${coverUrl}" alt="Episode ${i}">
                    <div class="episode-number">EP ${i}</div>
                    <div class="episode-duration">24:00</div>
                </div>
                <div class="episode-info">
                    <h4></h4>
                    <span>Episode ${i}</span>
                </div>
            `;

            // Gunakan textContent untuk mengatur judul anime
            const titleElement = episodeItem.querySelector('h4');
            if (titleElement) {
                titleElement.textContent = animeTitle;
            }

            episodeItem.addEventListener('click', () => {
                document.querySelectorAll('.episode-item').forEach(x => x.classList.remove('active'));
                episodeItem.classList.add('active');

                const titleH3 = document.querySelector('.video-title-info h3');
                const titleSpan = document.querySelector('.video-title-info span');
                if (titleH3) titleH3.textContent = animeTitle;
                if (titleSpan) titleSpan.textContent = `Episode ${i}`;

                const video = document.getElementById('animeVideo');
                if (video) {
                    video.currentTime = 0;
                    video.play();
                }
            });

            episodeList.appendChild(episodeItem);
        }
    }

    if (episodeList) {
        renderEpisodes();
    }

    if (seasonSelect) {
        seasonSelect.addEventListener('change', (e) => {
            renderEpisodes();
        });
    }

    /* ==================================================
       RATING SYSTEM - LOAD FROM DB & PERSIST
    ================================================== */
    const ratingSlider = document.getElementById('ratingSlider');
    const ratingNumber = document.getElementById('ratingNumber');
    const ratingText = document.getElementById('ratingText');
    const btnSubmitRating = document.getElementById('btnSubmitRating');
    
    let tempRating = 0;

    // ✅ Set rating awal dari DB
    if (ratingSlider && ratingNumber && ratingText && btnSubmitRating) {
        const initial = Math.max(0, Math.min(10, initialUserRating));
        ratingSlider.value = Math.round(initial * 10);
        ratingNumber.textContent = initial.toFixed(1);

        if (initial > 0) {
            ratingText.textContent = `Your current rating: ${initial.toFixed(1)}/10`;
            btnSubmitRating.disabled = false; // boleh update rating
        } else {
            ratingText.textContent = 'Drag slider to rate (0.0 - 10.0)';
            btnSubmitRating.disabled = true;
        }
        
        // Update slider color
        updateSliderColor(ratingSlider.value);
    }

    if (ratingSlider) {
        // slider 0-100 => rating 0.0-10.0
        ratingSlider.addEventListener('input', (e) => {
            const sliderValue = parseInt(e.target.value || "0", 10);
            tempRating = (sliderValue / 10).toFixed(1);

            ratingNumber.textContent = tempRating;
            ratingText.textContent = tempRating > 0 ? `Rate ${tempRating}/10` : 'Drag slider to rate (0.0 - 10.0)';
            if (btnSubmitRating) btnSubmitRating.disabled = !(tempRating > 0);
            
            // Update slider color
            updateSliderColor(sliderValue);
        });
    }
    
    function updateSliderColor(value) {
        if (!ratingSlider) return;
        const percentage = value;
        ratingSlider.style.background = `linear-gradient(to right, 
            #ff4444 0%, 
            #ff6b6b ${percentage * 0.2}%, 
            #ffa500 ${percentage * 0.4}%, 
            #ffd700 ${percentage * 0.6}%, 
            #90EE90 ${percentage * 0.8}%, 
            #00d900 100%)`;
    }

    // Function to submit rating to server
    async function submitRatingToServer(ratingVal) {
        const res = await fetch(rateApiUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                anime_id: parseInt(animeId, 10),
                rating: ratingVal
            })
        });

        const json = await res.json();
        if (!res.ok || json.status !== "success") {
            throw new Error(json.message || "Failed to save rating");
        }
        return json.rating;
    }

    if (btnSubmitRating) {
        btnSubmitRating.addEventListener('click', async () => {
            if (tempRating > 0) {
                try {
                    btnSubmitRating.disabled = true;
                    const saved = await submitRatingToServer(parseFloat(tempRating));

                    ratingNumber.textContent = Number(saved).toFixed(1);
                    ratingText.textContent = `Your current rating: ${Number(saved).toFixed(1)}/10`;

                    showNotification(`Rating saved: ${Number(saved).toFixed(1)}/10`, 'success');
                    btnSubmitRating.innerHTML = '<i class="fas fa-check-circle"></i><span>Rating Saved</span>';

                    setTimeout(() => {
                        btnSubmitRating.innerHTML = '<i class="fas fa-check"></i><span>Update Rating</span>';
                        btnSubmitRating.disabled = false; // boleh update lagi
                    }, 1500);
                } catch (e) {
                    btnSubmitRating.disabled = false;
                    showNotification(e.message || 'Failed to save rating', 'error');
                }
            }
        });
    }

    /* ==================================================
       FAVORITE & LIST BUTTONS
    ================================================== */
    const btnFavorite = document.getElementById('btnFavorite');
    const btnList = document.getElementById('btnList');
    let isFavorited = false;
    let isInList = false;

    if (btnFavorite) {
        btnFavorite.addEventListener('click', () => {
            isFavorited = !isFavorited;
            
            if (isFavorited) {
                btnFavorite.classList.add('active');
                btnFavorite.innerHTML = '<i class="fas fa-heart"></i><span>Added to Favorite</span>';
                showNotification('Anime added to favorites!', 'favorite');
            } else {
                btnFavorite.classList.remove('active');
                btnFavorite.innerHTML = '<i class="far fa-heart"></i><span>Add to Favorite</span>';
                showNotification('Anime removed from favorites!', 'success');
            }
        });
    }

    if (btnList) {
        btnList.addEventListener('click', () => {
            isInList = !isInList;
            
            if (isInList) {
                btnList.classList.add('active');
                btnList.innerHTML = '<i class="fas fa-plus"></i><span>Added to List</span>';
                showNotification('Anime added to your list!', 'success');
            } else {
                btnList.classList.remove('active');
                btnList.innerHTML = '<i class="fas fa-plus"></i><span>Add to List</span>';
                showNotification('Anime removed from your list!', 'success');
            }
        });
    }

    /* ==================================================
       LOAD INITIAL COMMENTS FROM DATABASE
    ================================================== */
    // Load initial comments
    reloadComments();

    /* ==================================================
       HEADER & NAVIGATION FUNCTIONALITY
    ================================================== */
    const header = document.getElementById('mainHeader');
    const backToTop = document.getElementById('backToTop');
    const searchTrigger = document.getElementById('searchTrigger');
    const searchOverlay = document.getElementById('searchOverlay');
    const searchClose = document.getElementById('searchClose');
    const mobileToggle = document.getElementById('mobileToggle');
    const navbar = document.getElementById('navbar');
    const userBtn = document.getElementById('userBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            if (header) header.classList.add('scrolled');
            if (backToTop) backToTop.classList.add('show');
        } else {
            if (header) header.classList.remove('scrolled');
            if (backToTop) backToTop.classList.remove('show');
        }
    });
    
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
        if(e.key === "Escape" && searchOverlay && searchOverlay.classList.contains('active')) {
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
    
    if (backToTop) {
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    /* ==================================================
       RECOMMENDATION INTERACTIONS
    ================================================== */
    const recommendationItems = document.querySelectorAll('.recommendation-item');
    
    recommendationItems.forEach(item => {
        item.addEventListener('click', function() {
            const title = this.querySelector('h4').textContent;
            showNotification(`Navigating to ${title}...`, 'success');
        });
    });

    console.log('Watch page initialized successfully!');
});