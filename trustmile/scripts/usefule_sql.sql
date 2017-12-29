SELECT datname,usename,pid,client_addr,waiting,query_start,query FROM pg_stat_activity ;


  -- Cancel all queries in an annoying database
	SELECT pg_cancel_backend(pid)
	FROM pg_stat_activity
	WHERE waiting is true;


	-- terminate process by annoying database
	SELECT pg_terminate_backend(procpid)
	FROM pg_stat_activity
	WHERE waiting is true;