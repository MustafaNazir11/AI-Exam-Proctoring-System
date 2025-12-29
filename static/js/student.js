document.addEventListener('DOMContentLoaded', function () {
    // ===================== QUIZ NAVIGATION LOGIC =====================
    const questionBlocks = document.querySelectorAll('.question-block');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.querySelector('.progress-bar');
    const currentQuestionSpan = document.getElementById('current-question');
    const totalQuestionsSpan = document.getElementById('total-questions');

    let current = 0;
    const totalQuestions = questionBlocks.length;

    totalQuestionsSpan.textContent = totalQuestions;

    function showQuestion(index) {
        questionBlocks.forEach((block, i) => {
            block.classList.remove('active');
            if (i === index) {
                setTimeout(() => block.classList.add('active'), 10);
            }
        });

        prevBtn.style.display = index > 0 ? 'inline-block' : 'none';
        nextBtn.style.display = index < totalQuestions - 1 ? 'inline-block' : 'none';
        submitBtn.style.display = index === totalQuestions - 1 ? 'inline-block' : 'none';

        const progress = ((index + 1) / totalQuestions) * 100;
        progressBar.style.width = `${progress}%`;
        currentQuestionSpan.textContent = index + 1;

        const options = questionBlocks[index].querySelectorAll('.option');
        options.forEach((option, i) => {
            option.style.animationDelay = `${i * 0.1}s`;
            option.classList.add('animate__animated', 'animate__fadeIn');
        });
    }

    nextBtn.addEventListener('click', () => {
        if (current < totalQuestions - 1) {
            current++;
            showQuestion(current);
        }
    });

    prevBtn.addEventListener('click', () => {
        if (current > 0) {
            current--;
            showQuestion(current);
        }
    });

    document.querySelectorAll('.option').forEach(option => {
        option.addEventListener('click', function () {
            const questionBlock = this.closest('.question-block');
            questionBlock.querySelectorAll('.option').forEach(opt => {
                opt.style.backgroundColor = '';
                opt.style.borderColor = '';
            });
            this.style.backgroundColor = 'rgba(74, 107, 255, 0.1)';
            this.style.borderColor = 'var(--primary)';
        });
    });

    document.getElementById('quiz-form').addEventListener('submit', function () {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        submitBtn.disabled = true;
    });

    showQuestion(current);

    // ===================== PROCTORING LOGIC =====================
    const video = document.getElementById("webcam");
    const violationDisplay = document.getElementById("violationDisplay");
    const examEnded = document.getElementById("examEnded");
    const quizContainer = document.querySelector(".quiz-container");
    let violationCount = 0;
    let peerId = null;
    let studentStream = null;

    // 🔗 Initialize PeerJS first
    const peer = new Peer({
        host: "0.peerjs.com",
        port: 443,
        secure: true
    });

    peer.on("open", id => {
        peerId = id;
        console.log("✅ Student Peer ID:", peerId);

        // Register peer ID with server
        fetch("/store-peer-id", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ peerId })
        }).then(() => {
            console.log("✅ Peer ID registered with server");
        }).catch(err => {
            console.error("❌ Failed to register peer ID:", err);
        });
    });

    // 🎥 Start webcam after PeerJS is ready
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
            video.srcObject = stream;
            studentStream = stream;
            console.log("✅ Student camera stream ready");

            // 🔥 Handle incoming calls from proctor
            peer.on("call", (call) => {
                console.log("📞 Incoming call from proctor:", call.peer);

                // Answer with current stream
                call.answer(studentStream);

                call.on('error', (err) => {
                    console.error("❌ Call error:", err);
                });

                call.on('close', () => {
                    console.log("📞 Call closed by proctor");
                });
            });

            // Auto-call proctor if available (for initial connection)
            setTimeout(() => {
                callProctor();
            }, 2000);

            // Check for reconnect requests every 2 seconds
            setInterval(() => {
                if (peerId) {
                    fetch(`/check-reconnect/${peerId}`)
                        .then(res => res.json())
                        .then(data => {
                            if (data.reconnect) {
                                console.log('🔄 Reconnect requested, calling proctor...');
                                callProctor();
                            }
                        })
                        .catch(err => console.error('Failed to check reconnect:', err));
                }
            }, 2000);
        })
        .catch(() => {
            alert("⚠️ Camera access denied. Exam cannot proceed.");
        });

    function callProctor() {
        fetch('/get-proctor-ids')
            .then(res => res.json())
            .then(proctorIds => {
                if (proctorIds.length > 0) {
                    const proctorId = proctorIds[0];
                    console.log("📞 Calling proctor:", proctorId);
                    const call = peer.call(proctorId, studentStream);

                    if (call) {
                        call.on('error', (err) => {
                            console.error("❌ Error calling proctor:", err);
                        });
                    }
                }
            })
            .catch(err => console.error('Failed to get proctor IDs:', err));
    }

    // 📸 Screenshot every 10s
    // 📸 Screenshot every 10s
    setInterval(() => {
        if (!peerId || !video.videoWidth || !video.videoHeight) return;

        // ⏱ Temporarily show webcam to avoid black image


        // Wait a moment to ensure frame is available
        setTimeout(() => {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

            const base64Image = canvas.toDataURL("image/png");


            fetch("/upload-screenshot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: base64Image, peerId })
            })
                .then(res => res.json())
                .then(data => {
                    console.log("✅ Screenshot uploaded to Cloudinary");
                    console.log("🌩️ Cloudinary URL:", data.cloudinary_url);

                    if (data.message?.includes("Suspicious")) {
                        violationCount++;

                        console.log("🚨 Violation Detected:", data.reasons.join(", "));
                        console.log("📸 Evidence URL:", data.cloudinary_url);
                        console.log("⚠️ Total Violations:", violationCount);

                        // Show styled popup with SweetAlert2
                        Swal.fire({
                            icon: 'warning',
                            title: 'Violation Detected!',
                            html: `
                <strong>Reason:</strong> ${data.reasons.join(", ")}<br>
                <strong>Total Violations:</strong> ${violationCount}
            `,
                            confirmButtonText: 'OK',
                            customClass: {
                                popup: 'violation-alert'
                            }
                        });

                        // Hide the image display
                        violationDisplay.style.display = "none";
                        violationDisplay.innerHTML = "";

                        if (data.action === "stop_exam") {
                            console.log("🛑 Exam forcibly ended due to violations.");
                            quizContainer.style.display = "none";
                            examEnded.style.display = "block";

                            const stream = video.srcObject;
                            if (stream) {
                                stream.getTracks().forEach(track => track.stop());
                                video.srcObject = null;
                            }

                            Swal.fire({
                                icon: 'error',
                                title: 'Exam Ended',
                                text: 'Exam forcibly terminated due to repeated violations.',
                                confirmButtonText: 'OK'
                            });
                        }
                    } else {
                        console.log("✅ Screenshot analyzed: No violation detected.");
                    }
                })


                .catch(err => console.error("Screenshot upload failed:", err));
        }, 500); // wait 100ms before capturing
    }, 3000);

});
