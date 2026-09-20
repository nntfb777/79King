var app = new Vue({
  el: '#app',
  data: {
    timeHanlde: null,
    tim: 0,
    masterUrls: [],
    urls: [],
    moburls: [],
    waitingText: "waiting",
    connectTimeout: "connect Timeout",
    connectFail: '3ms',
    name: '79king.com/',
    kefuUrl: "",
    apkAppUrl: "",
    pcUrl: "",
    socialLinks: {
      telegramUrl: "https://telegram.me/vuanhacai_79king",
      dailyTelegramUrl: "https://telegram.me/CSKH24H79KING",
      facebookUrl: "https://www.facebook.com/79kingThegioigiaitriso1/",
      agentLoginUrl: "http://fc.79king.auction/",
      giftcodeUrl: "https://79kingcode.pages.dev/"
    },
    banners: [
      "/images/banner/1.jpg",
      "/images/banner/2.jpg",
      "/images/banner/3.jpg",
      "/images/banner/4.jpg",
      "/images/banner/5.jpg",
      "/images/banner/6.jpg"
    ],
    apiUrl: "https://linksbackend.nnt79g.workers.dev/api/config?site_id=79king"
  },
  computed: {
    groupedBanners() {
      const pairs = [];
      if (!this.banners || this.banners.length === 0) return pairs;
      for (let i = 0; i < this.banners.length; i += 2) {
        pairs.push(this.banners.slice(i, i + 2));
      }
      return pairs;
    }
  },
  async mounted() {
    await this.fetchLinksFromApi();
    this.urls = this.getRandomUrls(5);
    this.moburls = this.getRandomUrls(5);
    this.startPingCheck();
  },
  methods: {
    async fetchLinksFromApi() {
      try {
        const res = await fetch(this.apiUrl);
        const result = await res.json();

        if (result.success && result.data) {
          const data = result.data;

          // 1. Cập nhật systemLinks (kefuUrl, apkAppUrl, pcUrl)
          if (data.systemLinks) {
            if (data.systemLinks.kefuUrl) this.kefuUrl = data.systemLinks.kefuUrl;
            if (data.systemLinks.apkAppUrl) this.apkAppUrl = data.systemLinks.apkAppUrl;
            if (data.systemLinks.pcUrl) this.pcUrl = data.systemLinks.pcUrl;
          }

          // 2. Cập nhật danh sách URL chính để ping (masterUrls)
          if (data.masterUrls && data.masterUrls.length > 0) {
            this.masterUrls = data.masterUrls;
            this.urls = this.getRandomUrls(5);
            this.moburls = this.getRandomUrls(5);
          }

          // 3. Cập nhật danh sách mạng xã hội (socialLinks)
          if (data.socialLinks) {
            Object.assign(this.socialLinks, data.socialLinks);
          }

          // 4. Cập nhật danh sách hình ảnh Banner
          if (data.banners && data.banners.length > 0) {
            this.banners = data.banners;
          }
        }
      } catch (err) {
        console.error("Lỗi tải link từ API:", err);
      }
    },
    getRandomUrls(count) {
      if (!this.masterUrls || this.masterUrls.length === 0) return [];
      const shuffled = this.masterUrls.slice().sort(() => 0.5 - Math.random());
      const selectedUrls = shuffled.slice(0, count);
      return selectedUrls.map((url, index) => {
        const fakeMs = Math.floor(Math.random() * (9 - 3 + 1)) + 3;
        return {
          url: url,
          title: `Link truy cập ${index + 1}`,
          second: fakeMs + 'ms',
          time: fakeMs
        };
      });
    },
    startPingCheck() {
      if (this.timeHanlde) clearInterval(this.timeHanlde);

      // Nhảy ms ngẫu nhiên từ 3ms đến 9ms liên tục mỗi 1.5 giây
      this.timeHanlde = setInterval(() => {
        if (this.urls && this.urls.length > 0) {
          this.urls.forEach(item => {
            const fakeMs = Math.floor(Math.random() * (9 - 3 + 1)) + 3;
            item.time = fakeMs;
            item.second = fakeMs + 'ms';
          });
        }
        if (this.moburls && this.moburls.length > 0) {
          this.moburls.forEach(item => {
            const fakeMs = Math.floor(Math.random() * (9 - 3 + 1)) + 3;
            item.time = fakeMs;
            item.second = fakeMs + 'ms';
          });
        }
      }, 1500);
    },
    refresh() {
      this.urls = this.getRandomUrls(5);
      this.moburls = this.getRandomUrls(5);
      this.startPingCheck();
    },
    sortOrder(filed, type = 'asc') {
      return (a, b) => {
        if (type === 'asc') return a[filed] > b[filed] ? 1 : -1;
        return a[filed] > b[filed] ? -1 : 1;
      };
    },
    sortList() {
      this.urls.sort(this.sortOrder('time', 'asc'));
      this.moburls.sort(this.sortOrder('time', 'asc'));
    },
    down() {
      if (this.browserDetection() == 'PC') {
        window.location.href = this.pcUrl || "https://79king.com";
      } else {
        if (this.browserDetection() == 'iphone' || this.browserDetection() == 'ipad') {
          window.location.href = this.apkAppUrl || "https://79k09.club/DownloadApp/";
        } else {
          window.location.href = this.apkAppUrl || "https://79k09.club/DownloadApp/";
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
        browser = 'midp';
      } else if (userAgent.match(/android/i)) {
        browser = 'android';
      } else {
        browser = 'PC';
      }
      return browser;
    }
  }
});
