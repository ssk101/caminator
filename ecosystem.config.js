module.exports = {
  apps: [
    {
      name: 'caminator',
      script: './caminator.js',
      watch: true,
      max_memory_restart: '1G',
      autorestart: true,
      restart_delay: 5000,
    }
  ]
}
