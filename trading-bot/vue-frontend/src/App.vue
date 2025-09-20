<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container">
        <router-link to="/" class="navbar-brand">
          <i class="bi bi-graph-up"></i> Kraken Trading Bot
        </router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/" class="nav-link">
                <i class="bi bi-house"></i> Dashboard
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/analysis" class="nav-link">
                <i class="bi bi-bar-chart"></i> Analysis
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/logs" class="nav-link">
                <i class="bi bi-journal-text"></i> Logs
              </router-link>
            </li>
            <li class="nav-item">
              <router-link to="/performance" class="nav-link">
                <i class="bi bi-trophy"></i> Performance
              </router-link>
            </li>
          </ul>
          <span class="navbar-text">
            <small class="text-light">
              <i class="bi bi-circle-fill text-success"></i> Connected
            </small>
          </span>
        </div>
      </div>
    </nav>

    <main class="container mt-4">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.navbar-brand {
  font-weight: bold;
}

.nav-link {
  font-weight: 500;
}

.card {
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border: none;
  margin-bottom: 1rem;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
}

.btn-primary:hover {
  background-color: #0056b3;
  border-color: #0056b3;
}

.table th {
  border-top: none;
  font-weight: 600;
  color: #495057;
}

.alert {
  border-radius: 0.375rem;
}

.chart-container {
  position: relative;
  height: 400px;
  width: 100%;
}
</style>