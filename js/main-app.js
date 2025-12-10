    var app = new Vue({
        el: '#app',
        data: {
            timeHanlde: null,
            tim: 0,
            
            masterUrls: [
                "https://goplay00.club/",  
                "https://goplay01.club/", 
                "https://goplay02.club/",   
                "https://goplay03.club/",  
                "https://goplay04.club/",   
                "https://goplay05.club/",   
                "https://goplay06.club/",   
                "https://goplay07.club/",    
                "https://goplay08.club/",
                "https://79k01.club/",
                "https://79k02.club/",
                "https://79k03.club/", 
                "https://79k04.club/", 
                "https://79k05.club/", 
                "https://79k06.club/", 
                "https://79k07.club/", 
                "https://79k08.club/", 
                "https://79k09.club/",
        ],

            urls: [],
            moburls: [], 

            waitingText: "đang kiểm duyệt ",
            connectTimeout: "hết hạn",
            connectFail: '9ms',
            name: 'okking.com/',
            kefuUrl: "https://irevpv.as713gq9.com/chatwindow.aspx?siteId=65002300&planId=b2ad9aea-b0f0-41f1-a803-f9325ff65563&CHATGROUP=1",
            apkAppUrl: 'https://79k09.club/DownloadApp/',
            pcUrl: 'https://79k09.club/DownloadApp/',
        },
        mounted() {
            // Khởi tạo danh sách URL ngẫu nhiên khi trang được tải
            this.urls = this.getRandomUrls(5);
            this.moburls = this.getRandomUrls(5);

            this.startPingCheck();
        },
        methods: {
            // 2. HÀM LẤY NGẪU NHIÊN 5 URL
            getRandomUrls(count) {
                // Sao chép masterUrls để tránh thay đổi mảng gốc
                const shuffled = this.masterUrls.slice().sort(() => 0.5 - Math.random());
                // Chọn 'count' phần tử đầu tiên
                const selectedUrls = shuffled.slice(0, count);

                // Chuyển đổi thành định dạng đối tượng mà Vue cần
                return selectedUrls.map((url, index) => ({
                    url: url,
                    title: `Link truy cập ${index + 1}`,
                    second: this.waitingText,
                    time: 0
                }));
            },
            
            // Hàm bắt đầu kiểm tra Ping (Tách riêng để dùng lại)
            startPingCheck() {
                this.timeHanlde = setInterval(() => {
                    this.tim++
                }, 100)
                for (let i = 0; i < this.urls.length; i++) {
                    this.send(this.urls[i].url, i, 'urls')
                }
                for (let j = 0; j < this.moburls.length; j++) {
                    this.send(this.moburls[j].url, j, 'moburls');
                }
                setTimeout(() => {
                    this.sortList(this.urls);
                    this.sortList(this.moburls);
                }, 1000)
            },

            refresh() {
                this.tim = 0
                clearInterval(this.timeHanlde)
                
                // CẬP NHẬT: Chọn lại URL ngẫu nhiên khi làm mới
                this.urls = this.getRandomUrls(5);
                this.moburls = this.getRandomUrls(5);
                
                this.startPingCheck();
            },
            
            // ... (Các phương thức khác giữ nguyên hoặc điều chỉnh nhỏ)
            sortOrder(filed, type = 'asc') {
                return (a, b) => {
                    if (type === 'asc') return a[filed] > b[filed] ? 1 : -1;
                    return a[filed] > b[filed] ? -1 : 1;
                }
            },
            sortList() {
                this.urls.sort(this.sortOrder('time', 'asc'))
                this.moburls.sort(this.sortOrder('time', 'asc'))
            },
            send(url, index, listName) { // Thêm listName để xác định mảng
                const _this = this
                $.ajax({
                    type: 'get',
                    url: url,
                    dataType: 'jsonp',
                    timeout: 1000,
                    complete: function (res) {
                        const targetList = _this[listName]; // Chọn mảng urls hoặc moburls
                        
                        if (res.status == 200) {
                            if (_this.tim > 5000) {
                                targetList[index].second = _this.connectTimeout;
                            }
                            else {
                                targetList[index].second = _this.tim + 'ms';
                            }
                            targetList[index].time = _this.tim;
                        }
                        else {
                            targetList[index].second = _this.connectFail;
                            targetList[index].time = 999999;
                        }
                    },
                })
            },
            // ... (Các phương thức down() và browserDetection() giữ nguyên)
            down() {
                if (this.browserDetection() == 'PC') {
                    window.location.href = this.pcUrl;
                } else {
                    if (this.browserDetection() == 'iphone' || this.browserDetection() == 'ipad') {
                        window.location.href = this.ios_step_1
                        setTimeout(() => {
                            window.location.href = this.ios_step_2
                        }, 2000)
                    } else {
                        window.location.href = this.apkAppUrl;
                    }
                }
            },
            browserDetection() {
                var userAgent = window.navigator.userAgent.toLowerCase();
                var browser = null;
                if (userAgent.match(/ipad/i)) {
                    browser = 'ipad';
                } else if (userAgent.match(/iphone os/i)) {
                    browser = 'iphone';
                } else if (userAgent.match(/midp/i)) {
                    browser = 'midp'
                } else if (userAgent.match(/rv:1.2.3.4/i)) {
                    browser = 'rv:1.2.3.4';
                } else if (userAgent.match(/ucweb/i)) {
                    browser = 'ucweb';
                } else if (userAgent.match(/android/i)) {
                    browser = 'android';
                } else if (userAgent.match(/windows ce/i)) {
                    browser = 'windowsCe';
                } else if (userAgent.match(/windows mobile/i)) {
                    browser = 'windowsMobile';
                } else {
                    browser = 'PC'
                }
                return browser;
            }
        }
    })
    document.addEventListener("DOMContentLoaded", function () {
        const txtElements = document.querySelectorAll(".txt");

        function updateRandomPing() {
            txtElements.forEach(element => {
                const randomPing = Math.floor(Math.random() * 10 + 1) + "ms";
                element.textContent = randomPing;
            });
        }

        updateRandomPing();

        setTimeout(() => {
            setInterval(updateRandomPing, 1000);
        }, 1000);
    });