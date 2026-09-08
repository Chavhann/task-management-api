import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
});

const getStoredToken = () => localStorage.getItem("token");

const getPriorityLabel = (priority) => {
  if (!priority) {
    return "Medium";
  }

  return priority.charAt(0).toUpperCase() + priority.slice(1);
};

const getCategoryLabel = (category) => {
  if (!category) {
    return "Other";
  }

  return category.charAt(0).toUpperCase() + category.slice(1);
};

const formatDueDate = (dueDate) => {
  if (!dueDate) {
    return "";
  }

  return new Date(`${dueDate}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

const getDueDateStatus = (task) => {
  if (!task.due_date || task.completed) {
    return null;
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dueDate = new Date(`${task.due_date}T00:00:00`);
  dueDate.setHours(0, 0, 0, 0);

  if (dueDate < today) {
    return "overdue";
  }

  if (dueDate.getTime() === today.getTime()) {
    return "today";
  }

  return "upcoming";
};

const getDueDateLabel = (task) => {
  const status = getDueDateStatus(task);

  if (status === "overdue") {
    return `Overdue · ${formatDueDate(task.due_date)}`;
  }

  if (status === "today") {
    return "Due today";
  }

  if (status === "upcoming") {
    return `Due ${formatDueDate(task.due_date)}`;
  }

  if (task.completed && task.due_date) {
    return `Due ${formatDueDate(task.due_date)}`;
  }

  return null;
};

function App() {
  const [token, setToken] = useState(getStoredToken);
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);

  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    username: "",
    email: "",
    password: "",
  });

  const [newTask, setNewTask] = useState({
    title: "",
    description: "",
    due_date: "",
    priority: "medium",
    category: "other",
  });

  const [editTask, setEditTask] = useState({
    title: "",
    description: "",
    due_date: "",
    priority: "medium",
    category: "other",
    completed: false,
  });

  const [editingId, setEditingId] = useState(null);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [taskError, setTaskError] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [completionTask, setCompletionTask] = useState(null);
  const [completionNote, setCompletionNote] = useState("");

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setTasks([]);
  };

  const handleAuthError = (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      setToken(null);
      setUser(null);
      setTasks([]);
      setAuthError("Session expired. Please log in again.");
      return;
    }

    setTaskError(
      error.response?.data?.detail || "Something went wrong. Please try again."
    );
  };

  const fetchUserAndTasks = async () => {
    if (!token) {
      return;
    }

    setLoading(true);
    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const [userResponse, tasksResponse] = await Promise.all([
        api.get("/me"),
        api.get("/tasks"),
      ]);

      setUser(userResponse.data);
      setTasks(tasksResponse.data);
    } catch (error) {
      handleAuthError(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchUserAndTasks();
    }
  }, [token]);

  const handleAuthSubmit = async (event) => {
    event.preventDefault();

    setAuthError("");
    setLoading(true);

    try {
      if (authMode === "register") {
        await api.post("/register", {
          username: authForm.username.trim(),
          email: authForm.email.trim(),
          password: authForm.password,
        });

        const loginResponse = await api.post("/login", {
          username: authForm.username.trim(),
          password: authForm.password,
        });

        const newToken = loginResponse.data.access_token;

        localStorage.setItem("token", newToken);
        setToken(newToken);
      } else {
        const response = await api.post("/login", {
          username: authForm.username.trim(),
          password: authForm.password,
        });

        const newToken = response.data.access_token;

        localStorage.setItem("token", newToken);
        setToken(newToken);
      }

      setAuthForm({
        username: "",
        email: "",
        password: "",
      });
    } catch (error) {
      setAuthError(
        error.response?.data?.detail ||
          "Authentication failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = async (event) => {
    event.preventDefault();

    if (!newTask.title.trim()) {
      return;
    }

    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.post("/tasks", {
        title: newTask.title.trim(),
        description: newTask.description.trim() || null,
        due_date: newTask.due_date || null,
        priority: newTask.priority,
        category: newTask.category,
      });

      setTasks((currentTasks) => [...currentTasks, response.data]);

      setNewTask({
        title: "",
        description: "",
        due_date: "",
        priority: "medium",
        category: "other",
      });
    } catch (error) {
      handleAuthError(error);
    }
  };

  const openEdit = (task) => {
    setEditingId(task.id);

    setEditTask({
      title: task.title,
      description: task.description || "",
      due_date: task.due_date || "",
      priority: task.priority || "medium",
      category: task.category || "other",
      completed: task.completed,
    });

    setTaskError("");
  };

  const closeEdit = () => {
    setEditingId(null);

    setEditTask({
      title: "",
      description: "",
      due_date: "",
      priority: "medium",
      category: "other",
      completed: false,
    });
  };

  const handleEditSubmit = async (event, taskId) => {
    event.preventDefault();

    if (!editTask.title.trim()) {
      return;
    }

    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.put(`/tasks/${taskId}`, {
        title: editTask.title.trim(),
        description: editTask.description.trim() || null,
        due_date: editTask.due_date || null,
        priority: editTask.priority,
        category: editTask.category,
        completed: editTask.completed,
      });

      setTasks((currentTasks) =>
        currentTasks.map((task) =>
          task.id === taskId ? response.data : task
        )
      );

      closeEdit();
    } catch (error) {
      handleAuthError(error);
    }
  };

  const handleDelete = async (taskId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this task?"
    );

    if (!confirmed) {
      return;
    }

    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      await api.delete(`/tasks/${taskId}`);

      setTasks((currentTasks) =>
        currentTasks.filter((task) => task.id !== taskId)
      );
    } catch (error) {
      handleAuthError(error);
    }
  };

  const openCompletionModal = (task) => {
    setCompletionTask(task);
    setCompletionNote("");
  };

  const closeCompletionModal = () => {
    setCompletionTask(null);
    setCompletionNote("");
  };

  const confirmCompletion = async () => {
    if (!completionTask) {
      return;
    }

    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.put(`/tasks/${completionTask.id}`, {
        completed: true,
        completion_note: completionNote.trim() || null,
      });

      setTasks((currentTasks) =>
        currentTasks.map((task) =>
          task.id === completionTask.id ? response.data : task
        )
      );

      closeCompletionModal();
    } catch (error) {
      handleAuthError(error);
    }
  };

  const toggleTaskCompletion = async (task) => {
    if (!task.completed) {
      openCompletionModal(task);
      return;
    }

    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.put(`/tasks/${task.id}`, {
        completed: false,
      });

      setTasks((currentTasks) =>
        currentTasks.map((currentTask) =>
          currentTask.id === task.id ? response.data : currentTask
        )
      );
    } catch (error) {
      handleAuthError(error);
    }
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesSearch =
        task.title.toLowerCase().includes(search.toLowerCase()) ||
        (task.description || "")
          .toLowerCase()
          .includes(search.toLowerCase());

      const matchesFilter =
        filter === "all" ||
        (filter === "pending" && !task.completed) ||
        (filter === "completed" && task.completed);

      return matchesSearch && matchesFilter;
    });
  }, [tasks, search, filter]);

  const completedCount = tasks.filter((task) => task.completed).length;
  const pendingCount = tasks.length - completedCount;

  const completionPercentage =
    tasks.length === 0
      ? 0
      : Math.round((completedCount / tasks.length) * 100);

  const overdueCount = tasks.filter(
    (task) => getDueDateStatus(task) === "overdue"
  ).length;

  if (!token) {
    return (
      <div className="auth-page">
        <div className="auth-showcase">
          <div className="brand-mark">✓</div>

          <div className="brand-name">TaskFlow</div>

          <h1>
            Organize your work.
            <br />
            Finish what matters.
          </h1>

          <p>
            A simple, focused task manager designed to help you plan,
            prioritize, and complete your work.
          </p>

          <div className="feature-list">
            <div className="feature-item">
              <span>✓</span>
              <div>
                <strong>Smart task management</strong>
                <small>Create, organize, and track your tasks.</small>
              </div>
            </div>

            <div className="feature-item">
              <span>✓</span>
              <div>
                <strong>Priorities & deadlines</strong>
                <small>Know what needs your attention next.</small>
              </div>
            </div>

            <div className="feature-item">
              <span>✓</span>
              <div>
                <strong>Progress tracking</strong>
                <small>See your progress and keep moving forward.</small>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-panel">
          <div className="auth-card">
            <div className="mobile-brand">
              <div className="brand-mark">✓</div>
              <div className="brand-name">TaskFlow</div>
            </div>

            <h2>
              {authMode === "login"
                ? "Welcome back"
                : "Create your account"}
            </h2>

            <p className="auth-subtitle">
              {authMode === "login"
                ? "Sign in to continue to your workspace."
                : "Start organizing your work today."}
            </p>

            {authError && <div className="error-message">{authError}</div>}

            <form onSubmit={handleAuthSubmit}>
              <div className="input-wrapper">
                <label htmlFor="username">Username</label>

                <input
                  id="username"
                  type="text"
                  value={authForm.username}
                  onChange={(event) =>
                    setAuthForm({
                      ...authForm,
                      username: event.target.value,
                    })
                  }
                  placeholder="Enter your username"
                  required
                />
              </div>

              {authMode === "register" && (
                <div className="input-wrapper">
                  <label htmlFor="email">Email</label>

                  <input
                    id="email"
                    type="email"
                    value={authForm.email}
                    onChange={(event) =>
                      setAuthForm({
                        ...authForm,
                        email: event.target.value,
                      })
                    }
                    placeholder="you@example.com"
                    required
                  />
                </div>
              )}

              <div className="input-wrapper">
                <label htmlFor="password">Password</label>

                <div className="password-wrapper">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={authForm.password}
                    onChange={(event) =>
                      setAuthForm({
                        ...authForm,
                        password: event.target.value,
                      })
                    }
                    placeholder="Enter your password"
                    required
                  />

                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="primary-button auth-button"
                disabled={loading}
              >
                {loading
                  ? "Please wait..."
                  : authMode === "login"
                    ? "Sign in"
                    : "Create account"}
              </button>
            </form>

            <div className="auth-switch">
              {authMode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}

              <button
                type="button"
                onClick={() => {
                  setAuthMode(
                    authMode === "login" ? "register" : "login"
                  );
                  setAuthError("");
                }}
              >
                {authMode === "login" ? "Create one" : "Sign in"}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">✓</div>
          <div className="brand-name">TaskFlow</div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            <span>▦</span>
            All Tasks
          </button>

          <button
            className={`nav-item ${filter === "pending" ? "active" : ""}`}
            onClick={() => setFilter("pending")}
          >
            <span>◷</span>
            Pending
          </button>

          <button
            className={`nav-item ${
              filter === "completed" ? "active" : ""
            }`}
            onClick={() => setFilter("completed")}
          >
            <span>✓</span>
            Completed
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="user-profile">
            <div className="avatar">
              {user?.username?.charAt(0).toUpperCase()}
            </div>

            <div className="user-details">
              <strong>{user?.username}</strong>
              <small>{user?.email}</small>
            </div>
          </div>

          <button className="logout-button" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>My Tasks</h1>
            <p>
              Stay organized and make progress every day.
            </p>
          </div>

          <div className="topbar-stats">
            <div className="mini-stat">
              <strong>{pendingCount}</strong>
              <span>Pending</span>
            </div>

            <div className="mini-stat">
              <strong>{completedCount}</strong>
              <span>Completed</span>
            </div>

            <div className="mini-stat">
              <strong>{overdueCount}</strong>
              <span>Overdue</span>
            </div>
          </div>
        </header>

        <section className="dashboard-grid">
          <div className="progress-card">
            <div className="progress-ring">
              <svg viewBox="0 0 120 120">
                <circle
                  className="progress-background"
                  cx="60"
                  cy="60"
                  r="48"
                />

                <circle
                  className="progress-value"
                  cx="60"
                  cy="60"
                  r="48"
                  style={{
                    strokeDasharray: `${completionPercentage * 3.0159} 301.59`,
                  }}
                />
              </svg>

              <div className="progress-center">
                <strong>{completionPercentage}%</strong>
                <span>Done</span>
              </div>
            </div>

            <div className="progress-info">
              <h3>Today's progress</h3>
              <p>
                {completedCount} of {tasks.length} tasks completed
              </p>
            </div>
          </div>
        </section>

        {taskError && <div className="error-message">{taskError}</div>}

        <section className="task-form-section">
          <form className="task-form" onSubmit={handleCreateTask}>
            <div className="input-wrapper">
              <label htmlFor="new-task-title">Task</label>

              <input
                id="new-task-title"
                type="text"
                value={newTask.title}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    title: event.target.value,
                  })
                }
                placeholder="What needs to be done?"
                required
              />
            </div>

            <div className="input-wrapper">
              <label htmlFor="new-task-description">
                Description
              </label>

              <input
                id="new-task-description"
                type="text"
                value={newTask.description}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    description: event.target.value,
                  })
                }
                placeholder="Add details..."
              />
            </div>

            <div className="input-wrapper due-date-input">
              <label htmlFor="new-task-due-date">Due date</label>

              <input
                id="new-task-due-date"
                type="date"
                value={newTask.due_date}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    due_date: event.target.value,
                  })
                }
              />
            </div>

            <div className="input-wrapper priority-input">
              <label htmlFor="new-task-priority">
                Priority
              </label>

              <select
                id="new-task-priority"
                value={newTask.priority}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    priority: event.target.value,
                  })
                }
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            <div className="input-wrapper category-input">
              <label htmlFor="new-task-category">
                Category
              </label>

              <select
                id="new-task-category"
                value={newTask.category}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    category: event.target.value,
                  })
                }
              >
                <option value="work">Work</option>
                <option value="development">Development</option>
                <option value="study">Study</option>
                <option value="personal">Personal</option>
                <option value="other">Other</option>
              </select>
            </div>

            <button
              type="submit"
              className="primary-button add-button"
            >
              + Add Task
            </button>
          </form>
        </section>

        <section className="task-toolbar">
          <div className="search-box">
            <span>⌕</span>

            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search tasks..."
            />
          </div>

          <div className="filter-buttons">
            <button
              className={filter === "all" ? "active" : ""}
              onClick={() => setFilter("all")}
            >
              All
            </button>

            <button
              className={filter === "pending" ? "active" : ""}
              onClick={() => setFilter("pending")}
            >
              Pending
            </button>

            <button
              className={filter === "completed" ? "active" : ""}
              onClick={() => setFilter("completed")}
            >
              Completed
            </button>
          </div>
        </section>

        <section className="task-list">
          {loading ? (
            <div className="empty-state">
              <h3>Loading tasks...</h3>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✓</div>
              <h3>No tasks found</h3>
              <p>
                {search
                  ? "Try a different search."
                  : "Add your first task to get started."}
              </p>
            </div>
          ) : (
            filteredTasks.map((task) => {
              const dueDateStatus = getDueDateStatus(task);
              const dueDateLabel = getDueDateLabel(task);

              if (editingId === task.id) {
                return (
                  <form
                    key={task.id}
                    className="task-card edit-card"
                    onSubmit={(event) =>
                      handleEditSubmit(event, task.id)
                    }
                  >
                    <div className="edit-inputs">
                      <div className="input-wrapper">
                        <label>Task</label>

                        <input
                          type="text"
                          value={editTask.title}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              title: event.target.value,
                            })
                          }
                          required
                        />
                      </div>

                      <div className="input-wrapper">
                        <label>Description</label>

                        <input
                          type="text"
                          value={editTask.description}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              description: event.target.value,
                            })
                          }
                        />
                      </div>

                      <div className="input-wrapper due-date-input">
                        <label>Due date</label>

                        <input
                          type="date"
                          value={editTask.due_date}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              due_date: event.target.value,
                            })
                          }
                        />
                      </div>

                      <div className="input-wrapper priority-input">
                        <label>Priority</label>

                        <select
                          value={editTask.priority}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              priority: event.target.value,
                            })
                          }
                        >
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                        </select>
                      </div>

                      <div className="input-wrapper category-input">
                        <label>Category</label>

                        <select
                          value={editTask.category}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              category: event.target.value,
                            })
                          }
                        >
                          <option value="work">Work</option>
                          <option value="development">
                            Development
                          </option>
                          <option value="study">Study</option>
                          <option value="personal">Personal</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                    </div>

                    <div className="edit-actions">
                      <button
                        type="submit"
                        className="primary-button"
                      >
                        Save Changes
                      </button>

                      <button
                        type="button"
                        className="secondary-button"
                        onClick={closeEdit}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                );
              }

              return (
                <article
                  key={task.id}
                  className={`task-card ${
                    dueDateStatus === "overdue" ? "overdue" : ""
                  } ${task.completed ? "completed" : ""}`}
                >
                  <div className="task-main">
                    <button
                      className={`task-checkbox ${
                        task.completed ? "checked" : ""
                      }`}
                      onClick={() => toggleTaskCompletion(task)}
                      aria-label={
                        task.completed
                          ? "Reopen task"
                          : "Complete task"
                      }
                    >
                      {task.completed ? "✓" : ""}
                    </button>

                    <div className="task-content">
                      <div className="task-title-row">
                        <h3>{task.title}</h3>

                        <span
                          className={`priority-badge ${task.priority}`}
                        >
                          <span>●</span>
                          {getPriorityLabel(task.priority)}
                        </span>

                        <span
                          className={`category-badge ${task.category}`}
                        >
                          {getCategoryLabel(task.category)}
                        </span>
                      </div>

                      {task.description && (
                        <p className="task-description">
                          {task.description}
                        </p>
                      )}

                      <div className="task-meta-row">
                        {dueDateLabel && (
                          <span
                            className={`due-date-badge ${
                              dueDateStatus || ""
                            }`}
                          >
                            ◷ {dueDateLabel}
                          </span>
                        )}

                        {task.completed_at && (
                          <span className="completed-badge">
                            ✓ Completed{" "}
                            {new Date(
                              task.completed_at
                            ).toLocaleString()}
                          </span>
                        )}
                      </div>

                      {task.completion_note && (
                        <div className="completion-note">
                          <strong>Completion note:</strong>{" "}
                          {task.completion_note}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="task-actions">
                    <button
                      className="icon-button"
                      onClick={() => openEdit(task)}
                      title="Edit task"
                    >
                      Edit
                    </button>

                    <button
                      className="icon-button delete"
                      onClick={() => handleDelete(task.id)}
                      title="Delete task"
                    >
                      Delete
                    </button>
                  </div>
                </article>
              );
            })
          )}
        </section>
      </main>

      {completionTask && (
        <div className="modal-overlay">
          <div className="modal-card">
            <button
              className="modal-close"
              onClick={closeCompletionModal}
            >
              ×
            </button>

            <div className="modal-icon">✓</div>

            <h2>Complete this task?</h2>

            <p>
              Mark <strong>{completionTask.title}</strong> as
              completed.
            </p>

            <div className="input-wrapper">
              <label htmlFor="completion-note">
                Completion note{" "}
                <span className="optional">(optional)</span>
              </label>

              <textarea
                id="completion-note"
                value={completionNote}
                onChange={(event) =>
                  setCompletionNote(event.target.value)
                }
                placeholder="What did you accomplish?"
                rows="4"
              />
            </div>

            <div className="modal-actions">
              <button
                className="secondary-button"
                onClick={closeCompletionModal}
              >
                Cancel
              </button>

              <button
                className="primary-button"
                onClick={confirmCompletion}
              >
                Complete Task
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;