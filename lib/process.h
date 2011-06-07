
#ifndef CAILIE_PROCESS_H
#define CAILIE_PROCESS_H

#include <pthread.h>
#include <vector>
#include "path.h"
#include "unit.h"
#include "messages.h"

#ifdef CA_MPI

#include "campi.h"
#define CA_RESERVED_PREFIX(path) (sizeof(CaPacket) + (path).get_size())

#else // CA_MPI not defined

#define CA_RESERVED_PREFIX(path) 0

#endif

class CaProcess;
class CaThread;

class CaJob  {
	public:
	CaJob(CaUnit *unit, CaTransition *transition) {
		this->unit = unit;
		this->transition = transition;
	}

	int test_and_fire(CaThread *thread);

	CaJob *next;

	protected:
	CaUnit *unit;
	CaTransition *transition;
};

class CaThread {
	public:
		CaThread();
		~CaThread();
		CaUnit * get_unit(const CaPath &path, int def_id); 
		CaUnit * get_local_unit(const CaPath &path, int def_id);
		void set_process(CaProcess *process) { this->process = process; }

		void start();
		void join();
		void run_scheduler();

		void add_message(CaMessage *message);
		int process_messages();

		void add_job(CaJob *job) {
			job->next = NULL;
			if (last_job) {
				last_job->next = job;
				last_job = job;
			} else {
				first_job = job;
				last_job = job;
			}
		}
		void quit_all();

		void send(const CaPath &path, int unit_id, int place_pos, const CaPacker &packer);
		CaProcess * get_process() const { return process; }
	protected:
		CaProcess *process;
		pthread_t thread;
		pthread_mutex_t messages_mutex;
		CaMessage *messages;
		CaJob *first_job;
		CaJob *last_job;

		#ifdef CA_MPI
		CaMpiRequests requests;
		#endif
};

class CaProcess {
	public:
		CaProcess(int process_id, int process_count, int threads_count, int defs_count, CaUnitDef **defs);
		virtual ~CaProcess() { delete [] threads; }
		void start();
		CaJob * create_jobs() const;

		CaUnitDef *get_def(int def_id) const { return defs[def_id]; }

		void inform_new_unit(CaUnitDef *def, CaUnit *unit);

		void send_barriers(pthread_barrier_t *barrier1, pthread_barrier_t *barrier2);

		int get_threads_count() const { return threads_count; }
		int get_units_count() const;
		int get_process_count() const { return process_count; }
		int get_process_id() const { return process_id; }
		void write_reports(FILE *out) const;
		void fire_transition(int transition_id, const CaPath &path);

		void quit_all();

		bool quit_flag;
	protected:
		int process_id;
		int process_count;
		int threads_count;
		int defs_count;
		CaUnitDef **defs;
		CaThread *threads;
};

#endif
