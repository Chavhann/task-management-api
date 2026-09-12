import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const KANBAN_COLUMNS = [
  {
    id: "todo",
    title: "TO DO",
  },
  {
    id: "in_progress",
    title: "IN PROGRESS",
  },
  {
    id: "in_review",
    title: "IN REVIEW",
  },
  {
    id: "completed",
    title: "COMPLETED",
  },
];

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
  if (!task || !task.due_date || task.completed) {
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
  if (!task) {
    return null;
  }

  const status = getDueDateStatus(task);

  if (status === "overdue") {
    return `Overdue - ${formatDueDate(task.due_date)}`;
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
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
const [teams, setTeams] = useState([]);
const [selectedTeamId, setSelectedTeamId] = useState(null);
const [teamMembers, setTeamMembers] = useState([]);
const [teamLoading, setTeamLoading] = useState(false);
const [memberSearch, setMemberSearch] = useState("");
const [memberResults, setMemberResults] = useState([]);
const [showTeamPanel, setShowTeamPanel] = useState(false);
  const [projectDashboard, setProjectDashboard] = useState(null);
  const [projectLoading, setProjectLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadNotificationCount, setUnreadNotificationCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notificationLoading, setNotificationLoading] = useState(false);
  const [managerDashboard, setManagerDashboard] = useState(null);
  const [managerDashboardLoading, setManagerDashboardLoading] = useState(false);
  const [showManagerDashboard, setShowManagerDashboard] = useState(false);

  const isManager = user?.role === "manager";

  const selectedTeam = teams.find(
    (team) => team.id === selectedTeamId
  );

  const selectedTeamMembership = teamMembers.find(
    (member) => member.user_id === user?.id
  );

  const isTeamHead = selectedTeamMembership?.role === "team_head";

  const displayRole = isManager
    ? "Manager"
    : isTeamHead
      ? "Team Head"
      : "Member";

  const canManageSelectedTeam =
    isManager ||
    isTeamHead ||
    selectedTeam?.owner_id === user?.id;

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
    assignee_id: "",
  });

  const [editTask, setEditTask] = useState({
    title: "",
    description: "",
    due_date: "",
    priority: "medium",
    category: "other",
    completed: false,
    assignee_id: "",
  });

  const [editingId, setEditingId] = useState(null);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [viewMode, setViewMode] = useState("board");
  const [calendarDate, setCalendarDate] = useState(new Date());

  const calendarYear = calendarDate.getFullYear();
  const calendarMonth = calendarDate.getMonth();

  const calendarMonthLabel = calendarDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  const calendarStart = new Date(calendarYear, calendarMonth, 1);
  const calendarEnd = new Date(calendarYear, calendarMonth + 1, 0);
  const calendarStartDay = calendarStart.getDay();
  const calendarDaysInMonth = calendarEnd.getDate();

  const calendarCells = [];

  for (let i = 0; i < calendarStartDay; i++) {
    calendarCells.push(null);
  }

  for (let day = 1; day <= calendarDaysInMonth; day++) {
    calendarCells.push(new Date(calendarYear, calendarMonth, day));
  }

  while (calendarCells.length % 7 !== 0) {
    calendarCells.push(null);
  }

  const getTasksForCalendarDay = (date) => {
    if (!date) {
      return [];
    }

    const dateKey = `${date.getFullYear()}-${String(
      date.getMonth() + 1
    ).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

    return filteredTasks.filter((task) => task.due_date === dateKey);
  };

  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [taskError, setTaskError] = useState("");

  const [showPassword, setShowPassword] = useState(false);

  const [completionTask, setCompletionTask] = useState(null);
  const [completionNote, setCompletionNote] = useState("");
  const [taskSubtasks, setTaskSubtasks] = useState({});
  const [taskComments, setTaskComments] = useState({});
  const [commentInputs, setCommentInputs] = useState({});
  const [editingCommentId, setEditingCommentId] = useState(null);
  const [editingCommentText, setEditingCommentText] = useState("");
  const [expandedSubtasks, setExpandedSubtasks] = useState({});
  const [taskProgress, setTaskProgress] = useState({});
  const [subtaskInputs, setSubtaskInputs] = useState({});

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

  const fetchManagerDashboard = async () => {
    if (!token || !isManager) {
      setManagerDashboard(null);
      return;
    }

    setManagerDashboardLoading(true);

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.get("/manager/dashboard");
      setManagerDashboard(response.data);
    } catch (error) {
      handleAuthError(error);
      setManagerDashboard(null);
    } finally {
      setManagerDashboardLoading(false);
    }
  };

  const fetchTeams = async () => {
  if (!token) return;

  try {
    const response = await api.get("/teams", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const loadedTeams = response.data;
    setTeams(loadedTeams);

    if (loadedTeams.length > 0) {
      setSelectedTeamId((currentId) => {
        if (currentId && loadedTeams.some((team) => team.id === currentId)) {
          return currentId;
        }
        return loadedTeams[0].id;
      });
    } else {
      setSelectedTeamId(null);
      setTeamMembers([]);
    }
  } catch (error) {
    handleAuthError(error);
  }
};

const fetchTeamMembers = async (teamId) => {
  if (!token || !teamId) return;

  setTeamLoading(true);

  try {
    const response = await api.get(`/teams/${teamId}/members`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    setTeamMembers(response.data);
  } catch (error) {
    handleAuthError(error);
  } finally {
    setTeamLoading(false);
  }
};

const searchTeamUsers = async (value) => {
  setMemberSearch(value);

  if (!token || value.trim().length < 2) {
    setMemberResults([]);
    return;
  }

  try {
    const response = await api.get("/users/search", {
      params: { q: value.trim() },
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    setMemberResults(response.data);
  } catch (error) {
    handleAuthError(error);
  }
};

const addTeamMember = async (userId) => {
  if (!token || !selectedTeamId) return;

  try {
    await api.post(
      `/teams/${selectedTeamId}/members`,
      {
        user_id: userId,
        role: "member",
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    setMemberSearch("");
    setMemberResults([]);
    await fetchTeamMembers(selectedTeamId);
  } catch (error) {
    handleAuthError(error);
  }
};

const removeTeamMember = async (userId) => {
  if (!token || !selectedTeamId) return;

  try {
    await api.delete(
      `/teams/${selectedTeamId}/members/${userId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    await fetchTeamMembers(selectedTeamId);
  } catch (error) {
    handleAuthError(error);
  }
};

const updateTeamMemberRole = async (userId, role) => {
  if (!token || !selectedTeamId || !isManager) return;

  try {
    await api.put(
      `/teams/${selectedTeamId}/members/${userId}`,
      { role },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    await fetchTeamMembers(selectedTeamId);
    await fetchManagerDashboard();
  } catch (error) {
    handleAuthError(error);
  }
};

const fetchUserAndTasks = async () => {
    if (!token) {
      return;
    }

    setLoading(true);
    setTaskError("");

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const [userResponse, tasksResponse, projectsResponse] =
        await Promise.all([
          api.get("/me"),
          api.get("/tasks"),
          api.get("/projects"),
        ]);

      const loadedProjects = projectsResponse.data;

      setUser(userResponse.data);

      setTasks(tasksResponse.data);
      setProjects(loadedProjects);

      if (loadedProjects.length > 0) {
        setSelectedProjectId((currentProjectId) => {
          const stillExists = loadedProjects.some(
            (project) => project.id === currentProjectId
          );

          return stillExists
            ? currentProjectId
            : loadedProjects[0].id;
        });
      } else {
        setSelectedProjectId(null);
        setProjectDashboard(null);
      }
    } catch (error) {
      handleAuthError(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    if (!token) {
      return;
    }

    setNotificationLoading(true);

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const [notificationsResponse, unreadResponse] =
        await Promise.all([
          api.get("/notifications"),
          api.get("/notifications/unread-count"),
        ]);

      setNotifications(notificationsResponse.data);
      setUnreadNotificationCount(unreadResponse.data.count);
    } catch (error) {
      handleAuthError(error);
    } finally {
      setNotificationLoading(false);
    }
  };

  const markNotificationRead = async (notificationId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.patch(
        `/notifications/${notificationId}`,
        { is_read: true }
      );

      setNotifications((current) =>
        current.map((notification) =>
          notification.id === notificationId
            ? response.data
            : notification
        )
      );

      setUnreadNotificationCount((current) =>
        Math.max(0, current - 1)
      );
    } catch (error) {
      handleAuthError(error);
    }
  };

  const deleteNotification = async (notificationId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      await api.delete(`/notifications/${notificationId}`);

      setNotifications((current) =>
        current.filter(
          (notification) => notification.id !== notificationId
        )
      );

      await fetchNotifications();
    } catch (error) {
      handleAuthError(error);
    }
  };
  const fetchProjectDashboard = async (projectId) => {
    if (!token || !projectId) {
      setProjectDashboard(null);
      return;
    }

    setProjectLoading(true);

    try {
      api.defaults.headers.common.Authorization = `Bearer ${token}`;

      const response = await api.get(
        `/projects/${projectId}/dashboard`
      );

      setProjectDashboard(response.data);
    } catch (error) {
      handleAuthError(error);
      setProjectDashboard(null);
    } finally {
      setProjectLoading(false);
    }
  };

  useEffect(() => {
  if (token) {
    fetchTeams();
  }
}, [token]);
useEffect(() => {
  if (token && isManager) {
    fetchManagerDashboard();
  } else {
    setManagerDashboard(null);
  }
}, [token, isManager]);


useEffect(() => {
  if (token && selectedTeamId) {
    fetchTeamMembers(selectedTeamId);
  }
}, [token, selectedTeamId]);

useEffect(() => {
    if (token) {
      fetchUserAndTasks();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchNotifications();
    }
  }, [token]);

  useEffect(() => {
    if (token && selectedProjectId) {
      fetchProjectDashboard(selectedProjectId);
    }
  }, [token, selectedProjectId]);
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

  const fetchSubtasks = async (taskId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      const response = await api.get(
        `/tasks/${taskId}/subtasks`
      );

      setTaskSubtasks((current) => ({
        ...current,
        [taskId]: response.data,
      }));
    } catch (error) {
      handleAuthError(error);
    }
  };
  const fetchComments = async (taskId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      const response = await api.get(
        `/tasks/${taskId}/comments`
      );

      setTaskComments((current) => ({
        ...current,
        [taskId]: response.data,
      }));
    } catch (error) {
      handleAuthError(error);
    }
  };
  const createComment = async (taskId) => {
    const content = (commentInputs[taskId] || "").trim();

    if (!content || !token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.post(`/tasks/${taskId}/comments`, {
        content,
      });

      setCommentInputs((current) => ({
        ...current,
        [taskId]: "",
      }));

      await fetchComments(taskId);
    } catch (error) {
      handleAuthError(error);
    }
  };
  const updateComment = async (commentId, taskId, content) => {
    const updatedContent = content.trim();

    if (!updatedContent || !token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.put(`/comments/${commentId}`, {
        content: updatedContent,
      });

      await fetchComments(taskId);
    } catch (error) {
      handleAuthError(error);
    }
  };

  const deleteComment = async (commentId, taskId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.delete(`/comments/${commentId}`);

      await fetchComments(taskId);
    } catch (error) {
      handleAuthError(error);
    }
  };
  const fetchTaskProgress = async (taskId) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      const response = await api.get(
        `/tasks/${taskId}/progress`
      );

      setTaskProgress((current) => ({
        ...current,
        [taskId]: response.data,
      }));
    } catch (error) {
      handleAuthError(error);
    }
  };
  const createSubtask = async (taskId) => {
    const title = (subtaskInputs[taskId] || "").trim();

    if (!title || !token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.post(`/tasks/${taskId}/subtasks`, {
        title,
      });

      setSubtaskInputs((current) => ({
        ...current,
        [taskId]: "",
      }));

      await fetchSubtasks(taskId);
      await fetchTaskProgress(taskId);
    } catch (error) {
      handleAuthError(error);
    }
  };
  const toggleSubtask = async (subtask) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.put(`/subtasks/${subtask.id}`, {
        completed: !subtask.completed,
      });

      await fetchSubtasks(subtask.task_id);
      await fetchTaskProgress(subtask.task_id);
      await fetchTaskProgress(subtask.task_id);
    } catch (error) {
      handleAuthError(error);
    }
  };
  const deleteSubtask = async (subtask) => {
    if (!token) {
      return;
    }

    try {
      api.defaults.headers.common.Authorization =
        `Bearer ${token}`;

      await api.delete(`/subtasks/${subtask.id}`);

      await fetchSubtasks(subtask.task_id);
      await fetchTaskProgress(subtask.task_id);
    } catch (error) {
      handleAuthError(error);
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
        assignee_id: newTask.assignee_id
          ? Number(newTask.assignee_id)
          : null,
      });

      setTasks((currentTasks) => [...currentTasks, response.data]);

      setNewTask({
        title: "",
        description: "",
        due_date: "",
        priority: "medium",
        category: "other",
        assignee_id: "",
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
      assignee_id: task.assignee_id ? String(task.assignee_id) : "",
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
      assignee_id: "",
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
        assignee_id: editTask.assignee_id
          ? Number(editTask.assignee_id)
          : null,
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

  const handleKanbanStatusChange = async (task, newStatus) => {
    if (task.status === newStatus) {
      return;
    }

    if (!token) {
      setTaskError("You are not authenticated. Please sign in again.");
      return;
    }

    setTaskError("");

    try {
      const response = await api.put(
        `/tasks/${task.id}`,
        {
          status: newStatus,
          completed: newStatus === "completed",
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setTasks((currentTasks) =>
        currentTasks.map((currentTask) =>
          currentTask.id === task.id ? response.data : currentTask
        )
      );

      if (selectedProjectId) {
        await fetchProjectDashboard(selectedProjectId);
      }
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
          <div className="brand-mark">TF</div>

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
              <span>-</span>
              <div>
                <strong>Smart task management</strong>
                <small>Create, organize, and track your tasks.</small>
              </div>
            </div>

            <div className="feature-item">
              <span>-</span>
              <div>
                <strong>Priorities & deadlines</strong>
                <small>Know what needs your attention next.</small>
              </div>
            </div>

            <div className="feature-item">
              <span>-</span>
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
              <div className="brand-mark">TF</div>
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
          <div className="brand-mark">TF</div>
          <div className="brand-name">TaskFlow</div>
        </div>

        <div className="project-selector">
          <label htmlFor="project-select">Workspace Project</label>

          <select
            id="project-select"
            value={selectedProjectId || ""}
            onChange={(event) =>
              setSelectedProjectId(
                event.target.value
                  ? Number(event.target.value)
                  : null
              )
            }
            disabled={projects.length === 0}
          >
            {projects.length === 0 ? (
              <option value="">No projects</option>
            ) : (
              projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))
            )}
          </select>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${filter === "all" ? "active" : ""}`}
            onClick={() => setFilter("all")}
          >
            <span>-</span>
            All Tasks
          </button>

          <button
            className={`nav-item ${filter === "pending" ? "active" : ""}`}
            onClick={() => setFilter("pending")}
          >
            <span>-</span>
            Pending
          </button>

          <button
            className={`nav-item ${
              filter === "completed" ? "active" : ""
            }`}
            onClick={() => setFilter("completed")}
          >
            <span>-</span>
            Completed
          </button>

          {isManager && (
            <button
              className={`nav-item ${
                showManagerDashboard ? "active" : ""
              }`}
              type="button"
              onClick={() => setShowManagerDashboard(true)}
            >
              <span>-</span>
              Manager Dashboard
            </button>
          )}
        </nav>

        <div className="sidebar-bottom">
          <div className="user-profile">
            <div className="avatar">
              {user?.username?.charAt(0).toUpperCase()}
            </div>

            <div className="user-details">
              <strong>{user?.username}</strong>
              <small>{user?.email}</small>
              <span className="user-role-badge">{displayRole}</span>
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
            <h1>
              {projectDashboard?.project_name || "My Tasks"}
            </h1>

            <p>
              {projectDashboard
                ? "Project overview and progress."
                : "Stay organized and make progress every day."}
            </p>
          </div>

          <div className="topbar-stats">
            <div className="mini-stat">
              <strong>
                {projectDashboard?.todo_tasks ?? pendingCount}
              </strong>
              <span>To Do</span>
            </div>

            <div className="mini-stat">
              <strong>
                {projectDashboard?.completed_tasks ?? completedCount}
              </strong>
              <span>Completed</span>
            </div>

            <div className="mini-stat">
              <strong>
                {projectDashboard?.overdue_tasks ?? overdueCount}
              </strong>
              <span>Overdue</span>
            </div>
          </div>
          <div className="notification-wrapper">
            <button
              className="notification-button"
              onClick={() => setShowNotifications((current) => !current)}
              aria-label="Notifications"
            >
              <span className="notification-icon">!
              </span>
              {unreadNotificationCount > 0 && (
                <span className="notification-badge">
                  {unreadNotificationCount > 99 ? "99+" : unreadNotificationCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="notification-dropdown">
                <div className="notification-dropdown-header">
                  <strong>Notifications</strong>
                  <span>{unreadNotificationCount} unread</span>
                </div>

                {notificationLoading ? (
                  <div className="notification-empty">Loading...</div>
                ) : notifications.length === 0 ? (
                  <div className="notification-empty">No notifications yet.</div>
                ) : (
                  <div className="notification-list">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`notification-item ${
                          notification.is_read ? "" : "unread"
                        }`}
                      >
                        <div className="notification-content">
                          <strong>{notification.title}</strong>
                          <p>{notification.message}</p>
                        </div>

                        <div className="notification-actions">
                          {!notification.is_read && (
                            <button
                              type="button"
                              onClick={() => markNotificationRead(notification.id)}
                            >
                              Read
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => deleteNotification(notification.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </header>

        {showManagerDashboard && isManager && (
          <section className="manager-dashboard">
            <div className="manager-dashboard-header">
              <div>
                <h2>Company Dashboard</h2>
                <p>Overview of teams, projects, tasks, and progress.</p>
              </div>

              <button
                type="button"
                className="secondary-button"
                onClick={() => setShowManagerDashboard(false)}
              >
                Back to Tasks
              </button>
            </div>

            {managerDashboardLoading ? (
              <div className="dashboard-empty">
                Loading company dashboard...
              </div>
            ) : !managerDashboard ? (
              <div className="dashboard-empty">
                Unable to load company dashboard.
              </div>
            ) : (
              <>
                <div className="manager-stats-grid">
                  <div className="manager-stat-card">
                    <span>Total Teams</span>
                    <strong>{managerDashboard.total_teams}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>Total Members</span>
                    <strong>{managerDashboard.total_members}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>Total Projects</span>
                    <strong>{managerDashboard.total_projects}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>Total Tasks</span>
                    <strong>{managerDashboard.total_tasks}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>Completed</span>
                    <strong>{managerDashboard.completed_tasks}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>In Progress</span>
                    <strong>{managerDashboard.in_progress_tasks}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>In Review</span>
                    <strong>{managerDashboard.in_review_tasks}</strong>
                  </div>

                  <div className="manager-stat-card">
                    <span>Overdue</span>
                    <strong>{managerDashboard.overdue_tasks}</strong>
                  </div>
                </div>

                <div className="manager-progress-card">
                  <div className="manager-progress-header">
                    <div>
                      <strong>Overall Progress</strong>
                      <span>
                        {managerDashboard.completed_tasks} of{" "}
                        {managerDashboard.total_tasks} tasks completed
                      </span>
                    </div>

                    <strong>{managerDashboard.progress}%</strong>
                  </div>

                  <div className="manager-progress-track">
                    <div
                      className="manager-progress-fill"
                      style={{
                        width: `${managerDashboard.progress}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="manager-teams-section">
                  <div className="manager-dashboard-header">
                    <div>
                      <h3>Team Performance</h3>
                      <p>Progress across every company team.</p>
                    </div>
                  </div>

                  {managerDashboard.teams.length === 0 ? (
                    <div className="dashboard-empty">
                      No teams have been created yet.
                    </div>
                  ) : (
                    <div className="manager-team-grid">
                      {managerDashboard.teams.map((team) => (
                        <div
                          className="manager-team-card"
                          key={team.team_id}
                        >
                          <div className="manager-team-header">
                            <div>
                              <h4>{team.team_name}</h4>
                              <span>
                                {team.member_count} members ?{" "}
                                {team.project_count} projects
                              </span>
                            </div>

                            <strong>{team.progress}%</strong>
                          </div>

                          <div className="manager-progress-track">
                            <div
                              className="manager-progress-fill"
                              style={{
                                width: `${team.progress}%`,
                              }}
                            />
                          </div>

                          <div className="manager-team-stats">
                            <span>
                              <strong>{team.total_tasks}</strong> tasks
                            </span>

                            <span>
                              <strong>{team.completed_tasks}</strong> completed
                            </span>

                            <span>
                              <strong>{team.in_progress_tasks}</strong> active
                            </span>

                            <span>
                              <strong>{team.overdue_tasks}</strong> overdue
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        )}


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
                    strokeDasharray: `${
                      (projectDashboard?.progress ?? completionPercentage) *
                      3.0159
                    } 301.59`,
                  }}
                />
              </svg>

              <div className="progress-center">
                <strong>
                  {projectDashboard?.progress ?? completionPercentage}%
                </strong>
                <span>Done</span>
              </div>
            </div>

            <div className="progress-info">
              <h3>
                {projectDashboard
                  ? `${projectDashboard.project_name} progress`
                  : "Today's progress"}
              </h3>

              <p>
                {projectDashboard
                  ? `${projectDashboard.completed_tasks} of ${projectDashboard.total_tasks} tasks completed`
                  : `${completedCount} of ${tasks.length} tasks completed`}
              </p>

              {projectDashboard && (
                <small>
                  {projectDashboard.in_progress_tasks} in progress  {" "}
                  {projectDashboard.in_review_tasks} in review
                </small>
              )}
            </div>
          </div>
        </section>
        {projectDashboard && (
          <section className="project-activity-section">
            <div className="section-header">
              <div>
                <span className="section-eyebrow">RECENT ACTIVITY</span>
                <h2>Project Activity</h2>
                <p>Latest actions in this project.</p>
              </div>
            </div>

            {projectLoading ? (
              <div className="activity-empty">Loading activity...</div>
            ) : projectDashboard.recent_activity?.length ? (
              <div className="activity-list">
                {projectDashboard.recent_activity.map((activity) => (
                  <div className="activity-item" key={activity.id}>
                <div className="activity-dot">+</div>
                    <div className="activity-details">
                      <strong>{activity.description}</strong>
                      <span>
                        {new Date(activity.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="activity-empty">No recent activity.</div>
            )}
          </section>
        )}
        <section className="team-management-section">
  <div className="team-management-header">
    <div>
      <span className="section-eyebrow">TEAM WORKSPACE</span>
      <h2>
        {teams.find((team) => team.id === selectedTeamId)?.name || "Team"}
      </h2>
      <p>
        {teamMembers.length} {teamMembers.length === 1 ? "member" : "members"}
        {" "}in this workspace
      </p>
    </div>

    <div className="team-management-actions">
      <select
        value={selectedTeamId || ""}
        onChange={(event) => {
          setSelectedTeamId(Number(event.target.value));
        }}
        disabled={teams.length === 0}
      >
        {teams.length === 0 ? (
          <option value="">No teams</option>
        ) : (
          teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))
        )}
      </select>

      {canManageSelectedTeam && (
        <button
          type="button"
          className="secondary-button"
          onClick={() => setShowTeamPanel((current) => !current)}
        >
          {showTeamPanel ? "Hide Members" : "Manage Team"}
        </button>
      )}
    </div>
  </div>

  {showTeamPanel && (
    <div className="team-members-panel">
      <div className="team-members-list">
        {teamLoading ? (
          <div className="team-empty">Loading members...</div>
        ) : teamMembers.length === 0 ? (
          <div className="team-empty">No members found.</div>
        ) : (
          teamMembers.map((member) => {
            const selectedTeam = teams.find(
              (team) => team.id === selectedTeamId
            );
            const canManage = canManageSelectedTeam;

            return (
              <div className="team-member-row" key={member.id}>
                <div className="team-member-avatar">
                  {member.username.charAt(0).toUpperCase()}
                </div>

                <div className="team-member-info">
                  <strong>{member.username}</strong>
                  <span>{member.email}</span>
                </div>

                <span className={`team-role role-${member.role}`}>
                  {member.role}
                </span>

                {isManager &&
                  member.user_id !== user.id &&
                  member.role !== "admin" && (
                    <button
                      type="button"
                      className="member-role-button"
                      onClick={() =>
                        updateTeamMemberRole(
                          member.user_id,
                          member.role === "team_head" ? "member" : "team_head"
                        )
                      }
                    >
                      {member.role === "team_head"
                        ? "Make Member"
                        : "Make Team Head"}
                    </button>
                  )}

                {canManage &&
                  member.user_id !== user.id &&
                  member.role !== "admin" && (
                    <button
                      type="button"
                      className="member-remove-button"
                      onClick={() => removeTeamMember(member.user_id)}
                    >
                      Remove
                    </button>
                  )}
              </div>
            );
          })
        )}
      </div>

      {(() => {
        const selectedTeam = teams.find(
          (team) => team.id === selectedTeamId
        );

        if (!selectedTeam || !user || !canManageSelectedTeam) {
          return null;
        }

        return (
          <div className="add-member-box">
            <h3>Add team member</h3>

            <input
              type="text"
              value={memberSearch}
              onChange={(event) => searchTeamUsers(event.target.value)}
              placeholder="Search username or email..."
            />

            {memberResults.length > 0 && (
              <div className="member-search-results">
                {memberResults.map((result) => {
                  const alreadyMember = teamMembers.some(
                    (member) => member.user_id === result.id
                  );

                  return (
                    <div className="member-search-result" key={result.id}>
                      <div>
                        <strong>{result.username}</strong>
                        <span>{result.email}</span>
                      </div>

                      <button
                        type="button"
                        disabled={alreadyMember}
                        onClick={() => addTeamMember(result.id)}
                      >
                        {alreadyMember ? "Added" : "Add"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })()}
    </div>
  )}
</section>

<section className="kanban-section">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">WORKSPACE BOARD</span>
              <h2>{projectDashboard?.project_name ?? "Task Board"}</h2>
              <p>Drag tasks between columns to update their status.</p>
            </div>

            <div className="view-toggle">
              <button
                type="button"
                className={viewMode === "board" ? "active" : ""}
                onClick={() => setViewMode("board")}
              >
                Board
              </button>

              <button
                type="button"
                className={viewMode === "table" ? "active" : ""}
                onClick={() => setViewMode("table")}
              >
                Table
              </button>
              <button
                type="button"
                className={viewMode === "calendar" ? "active" : ""}
                onClick={() => setViewMode("calendar")}
              >
                Calendar
              </button>
            </div>

            <div className="board-summary">
              <span>
                {filteredTasks.length}{" "}
                {filteredTasks.length === 1 ? "task" : "tasks"}
              </span>
            </div>
          </div>

          {viewMode === "board" ? (
            <div className="kanban-board">
            {KANBAN_COLUMNS.map((column) => {
              const columnTasks = filteredTasks.filter(
                (task) => task.status === column.id
              );

              return (
                <div
                  key={column.id}
                  className="kanban-column"
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) => {
                    event.preventDefault();

                    const taskId = Number(
                      event.dataTransfer.getData("taskId")
                    );

                    const draggedTask = filteredTasks.find(
                      (task) => task.id === taskId
                    );

                    if (draggedTask) {
                      handleKanbanStatusChange(
                        draggedTask,
                        column.id
                      );
                    }
                  }}
                >
                  <div className="kanban-column-header">
                    <div className="kanban-column-title">
                      <span
                        className={`status-dot status-${column.id}`}
                      />
                      <h3>{column.title}</h3>
                    </div>

                    <span className="kanban-count">
                      {columnTasks.length}
                    </span>
                  </div>

                  <div className="kanban-column-body">
                    {columnTasks.length === 0 ? (
                      <div className="kanban-empty">
                        <span>No tasks</span>
                      </div>
                    ) : (
                      columnTasks.map((task) => (
                        <article
                          key={task.id}
                          className="kanban-card"
                          draggable
                          onDragStart={(event) => {
                            event.dataTransfer.setData(
                              "taskId",
                              String(task.id)
                            );
                            event.dataTransfer.effectAllowed = "move";
                          }}
                        >
                          <div className="kanban-card-top">
                            <span
                              className={`priority-badge priority-${task.priority}`}
                            >
                              {getPriorityLabel(task.priority)}
                            </span>

                            <span className="kanban-task-id">
                              #{task.id}
                            </span>
                          </div>

                          <h4>{task.title}</h4>

                          {task.description && (
                            <p className="kanban-description">
                              {task.description}
                            </p>
                          )}

                          {task.assignee && (
                            <div className="kanban-card-assignee">
                              <span className="assignee-avatar">
                                {task.assignee.username.charAt(0).toUpperCase()}
                              </span>
                              <span>{task.assignee.username}</span>
                            </div>
                          )}

                          <div className="kanban-card-meta">
                            <span>
                              {getDueDateLabel(task)}
                            </span>

                            <span>
                              {getCategoryLabel(task.category)}
                            </span>
                          </div>

                          <div className="kanban-card-actions">
                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() => openEdit(task)}
                            >
                              Edit
                            </button>

                            <button
                              type="button"
                              className="danger-button"
                              onClick={() => handleDelete(task.id)}
                            >
                              Delete
                            </button>
                          </div>
                        </article>
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          ) : viewMode === "calendar" ? (
            <div className="calendar-view">
              <div className="calendar-header">
                <button
                  type="button"
                  className="calendar-nav-button"
                  onClick={() =>
                    setCalendarDate(
                      new Date(calendarYear, calendarMonth - 1, 1)
                    )
                  }
                >
                  Previous
                </button>

                <h2>{calendarMonthLabel}</h2>

                <button
                  type="button"
                  className="calendar-nav-button"
                  onClick={() =>
                    setCalendarDate(
                      new Date(calendarYear, calendarMonth + 1, 1)
                    )
                  }
                >
                  Next
                </button>
              </div>

              <div className="calendar-weekdays">
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map(
                  (day) => (
                    <div key={day} className="calendar-weekday">
                      {day}
                    </div>
                  )
                )}
              </div>

              <div className="calendar-grid">
                {calendarCells.map((date, index) => {
                  const dayTasks = getTasksForCalendarDay(date);

                  return (
                    <div
                      key={date ? date.toISOString() : `empty-${index}`}
                      className={`calendar-cell${date ? "" : " empty"}`}
                    >
                      {date && (
                        <>
                          <div className="calendar-day-number">
                            {date.getDate()}
                          </div>

                          <div className="calendar-tasks">
                            {dayTasks.map((task) => (
                              <div
                                key={task.id}
                                className="calendar-task"
                                title={task.title}
                              >
                                {task.title}
                              </div>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="task-table-wrapper">
              <table className="task-table">
                <thead>
                  <tr>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Category</th>
                    <th>Assignee</th>
                    <th>Due date</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredTasks.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="task-table-empty">
                        No tasks found for this project.
                      </td>
                    </tr>
                  ) : (
                    filteredTasks.map((task) => (
                      <tr key={task.id}>
                        <td>
                          <div className="table-task-title">
                            {task.title}
                          </div>

                          {task.description && (
                            <div className="table-task-description">
                              {task.description}
                            </div>
                          )}
                        </td>

                        <td>
                          <span
                            className={`table-status status-${task.status}`}
                          >
                            {task.status.replace("_", " ")}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`priority-badge priority-${task.priority}`}
                          >
                            {getPriorityLabel(task.priority)}
                          </span>
                        </td>

                        <td>
                          {getCategoryLabel(task.category)}
                        </td>

                        <td>
                          {task.assignee ? (
                            <div className="table-assignee">
                              <span className="table-assignee-avatar">
                                {task.assignee.username.charAt(0).toUpperCase()}
                              </span>
                              <span>{task.assignee.username}</span>
                            </div>
                          ) : (
                            <span className="table-unassigned">Unassigned</span>
                          )}
                        </td>

                        <td>
                          {task.due_date
                            ? formatDueDate(task.due_date)
                            : "No due date"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
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

            <div className="input-wrapper assignee-input">
              <label htmlFor="new-task-assignee">
                Assignee
              </label>

              <select
                id="new-task-assignee"
                value={newTask.assignee_id}
                onChange={(event) =>
                  setNewTask({
                    ...newTask,
                    assignee_id: event.target.value,
                  })
                }
                disabled={!selectedTeamId || teamMembers.length === 0}
              >
                <option value="">
                  {teamMembers.length === 0
                    ? "No team members"
                    : "Unassigned"}
                </option>

                {teamMembers.map((member) => (
                  <option
                    key={member.user_id}
                    value={member.user_id}
                  >
                    {member.username}
                  </option>
                ))}
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
            <span>-</span>

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
              <div className="empty-icon">OK</div>
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

                      <div className="input-wrapper assignee-input">
                        <label>Assignee</label>
                        <select
                          value={editTask.assignee_id}
                          onChange={(event) =>
                            setEditTask({
                              ...editTask,
                              assignee_id: event.target.value,
                            })
                          }
                        >
                          <option value="">Unassigned</option>
                          {teamMembers.map((member) => (
                            <option key={member.user_id} value={member.user_id}>
                              {member.username}
                            </option>
                          ))}
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
                  } ${task.completed ? "OK" : ""}`}
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
                      {task.completed ? "OK" : ""}
                    </button>

                    <div className="task-content">
                      <div className="task-title-row">
                        <h3>{task.title}</h3>

                        <span
                          className={`priority-badge ${task.priority}`}
                        >
                          <span>-</span>
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
                            - {dueDateLabel}
                          </span>
                        )}

                        {task.completed_at && (
                          <span className="completed-badge">
                            OK Completed{" "}
                            {new Date(
                              task.completed_at
                            ).toLocaleString()}
                          </span>
                        )}
                      </div>

                      <div className="subtasks-section">
                        <div className="subtasks-header">
                          <button
                            type="button"
                            className="subtasks-toggle"
                            onClick={async () => {
                              const isExpanded =
                                expandedSubtasks[task.id];

                              setExpandedSubtasks((current) => ({
                                ...current,
                                [task.id]: !isExpanded,
                              }));

                              if (!isExpanded) {
                                await fetchSubtasks(task.id);
                                await fetchTaskProgress(task.id);
                              }
                            }}
                          >
                            <span>
                              Subtasks
                            </span>
                            <span className="subtasks-progress-text">
                              {taskProgress[task.id]
                                ? `${taskProgress[task.id].completed_subtasks} / ${taskProgress[task.id].total_subtasks}`
                                : "0 / 0"}
                            </span>
                          </button>

                          {taskProgress[task.id] && (
                            <div className="subtasks-progress">
                              <div className="subtasks-progress-bar">
                                <div
                                  className="subtasks-progress-fill"
                                  style={{
                                    width: `${taskProgress[task.id].progress}%`,
                                  }}
                                />
                              </div>
                              <span>
                                {taskProgress[task.id].progress}%
                              </span>
                            </div>
                          )}
                        </div>

                        {expandedSubtasks[task.id] && (
                          <div className="subtasks-list">
                            {(taskSubtasks[task.id] || []).map(
                              (subtask) => (
                                <div
                                  key={subtask.id}
                                  className={`subtask-item ${
                                    subtask.completed
                                      ? "completed"
                                      : ""
                                  }`}
                                >
                                  <button
                                    type="button"
                                    className="subtask-check"
                                    onClick={() =>
                                      toggleSubtask(subtask)
                                    }
                                    title={
                                      subtask.completed
                                        ? "Mark incomplete"
                                        : "Mark complete"
                                    }
                                  >
                                  </button>

                                  <span className="subtask-title">
                                    {subtask.title}
                                  </span>

                                  <button
                                    type="button"
                                    className="subtask-delete"
                                    onClick={() =>
                                      deleteSubtask(subtask)
                                    }
                                    title="Delete subtask"
                                  >
                                    Delete
                                  </button>
                                </div>
                              )
                            )}

                            <div className="subtask-add-row">
                              <input
                                type="text"
                                placeholder="Add a subtask..."
                                value={subtaskInputs[task.id] || ""}
                                onChange={(event) =>
                                  setSubtaskInputs((current) => ({
                                    ...current,
                                    [task.id]: event.target.value,
                                  }))
                                }
                                onKeyDown={(event) => {
                                  if (event.key === "Enter") {
                                    event.preventDefault();
                                    createSubtask(task.id);
                                  }
                                }}
                              />

                              <button
                                type="button"
                                onClick={() =>
                                  createSubtask(task.id)
                                }
                              >
                                Add
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="comments-section">
              <div className="comments-header">
                <button
                  type="button"
                  className="comments-toggle"
                  onClick={async () => {
                    await fetchComments(task.id);
                  }}
                >
                  <span>Discussion</span>
                  <span className="comments-count">
                    {taskComments[task.id]
                      ? taskComments[task.id].length
                      : "0"}
                  </span>
                </button>
              </div>

              <div className="comments-list">
                {(taskComments[task.id] || []).map(
                  (comment) => (
                    <div
                      key={comment.id}
                      className="comment-item"
                    >
                      <div className="comment-avatar">
                        {(comment.user?.username || "U").charAt(0).toUpperCase()}
                      </div>

                      <div className="comment-content">
                        <div className="comment-meta">
                          <span className="comment-author">
                            {comment.user?.username || `User ${comment.user_id}`}
                          </span>

                          <span className="comment-time">
                            {new Date(
                              comment.created_at
                            ).toLocaleString()}
                          </span>
                        </div>

                        {editingCommentId === comment.id ? (
                          <div className="comment-edit-row">
                            <input
                              type="text"
                              value={editingCommentText}
                              onChange={(event) =>
                                setEditingCommentText(
                                  event.target.value
                                )
                              }
                              onKeyDown={async (event) => {
                                if (event.key === "Enter") {
                                  event.preventDefault();

                                  await updateComment(
                                    comment.id,
                                    task.id,
                                    editingCommentText
                                  );

                                  setEditingCommentId(null);
                                  setEditingCommentText("");
                                }

                                if (event.key === "Escape") {
                                  setEditingCommentId(null);
                                  setEditingCommentText("");
                                }
                              }}
                              autoFocus
                            />

                            <button
                              type="button"
                              onClick={async () => {
                                await updateComment(
                                  comment.id,
                                  task.id,
                                  editingCommentText
                                );

                                setEditingCommentId(null);
                                setEditingCommentText("");
                              }}
                            >
                              Save
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setEditingCommentId(null);
                                setEditingCommentText("");
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <>
                            <p className="comment-text">
                              {comment.content}
                            </p>

                            {comment.user_id === user?.id && (
                              <div className="comment-actions">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingCommentId(
                                      comment.id
                                    );
                                    setEditingCommentText(
                                      comment.content
                                    );
                                  }}
                                >
                                  Edit
                                </button>

                                <button
                                  type="button"
                                  onClick={() =>
                                    deleteComment(
                                      comment.id,
                                      task.id
                                    )
                                  }
                                >
                                  Delete
                                </button>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  )
                )}

                <div className="comment-add-row">
                  <input
                    type="text"
                    placeholder="Write a comment..."
                    value={commentInputs[task.id] || ""}
                    onChange={(event) =>
                      setCommentInputs((current) => ({
                        ...current,
                        [task.id]: event.target.value,
                      }))
                    }
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        createComment(task.id);
                      }
                    }}
                  />

                  <button
                    type="button"
                    onClick={() => createComment(task.id)}
                  >
                    Comment
                  </button>
                </div>
              </div>
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
              x
            </button>

            <div className="modal-icon">!</div>

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
