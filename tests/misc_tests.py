import CPtest


class MiscTest(CPtest.CPTest):
    def test_whoishere(self):
        with self.patch_session():
            self.getPage("/whoishere")
        self.assertStatus('200 OK')

    def test_index(self):
        with self.patch_session():
            self.getPage("/")
        self.assertStatus('200 OK')

    def test_service_worker_served_from_root(self):
        self.getPage("/sw.js")
        self.assertStatus('200 OK')
        self.assertHeaderIn('Content-Type', ['text/javascript;charset=utf-8'])
        self.assertHeader('Cache-Control', 'no-cache')
        self.assertInBody("addEventListener('fetch'")

    def test_links(self):
        with self.patch_session():
            self.getPage("/links")
        self.assertStatus('200 OK')

    def test_links_full(self):
        with self.patch_session():
            self.getPage("/links?barcode=100091")
            self.assertStatus('200 OK')

    def test_metrics(self):
        with self.patch_session():
            self.getPage("/metrics")
            self.assertStatus('200 OK')

    def test_unlock(self):
        with self.patch_session():
            self.getPage("/unlock?location=TFI&barcode=100091")
        self.assertStatus('303 See Other')
