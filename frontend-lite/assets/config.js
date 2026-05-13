window.CYBER_AGENT_CONFIG = {
  /*
   * 如果前端和后端部署在同一台服务器：
   * 默认会自动请求：
   * http://当前服务器IP:8000
   *
   * 如果你想手动指定后端地址，取消下面这行注释：
   */
  // API_BASE_URL: 'http://你的服务器IP:8000',

  /*
   * 如果你后端关闭了鉴权：
   * config/config.example.yaml 里 auth.enabled=false
   * 这里不用配置 token。
   *
   * 如果后端还开启鉴权，可以填 token：
   */
      API_BASE_URL: 'http://123.60.55.113:8000',
  TOKEN: '',
}