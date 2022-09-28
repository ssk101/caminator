module.exports = {
  apps: [
    {
      name: 'caminator',
      script: './caminator.js',
      watch: false,
      max_memory_restart: '1G',
      autorestart: true,
      restart_delay: 5000,
    }
  ]
}
