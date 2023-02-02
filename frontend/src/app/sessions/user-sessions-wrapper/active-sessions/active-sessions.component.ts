/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Session } from 'src/app/schemes';
import { BeautifyService } from 'src/app/services/beatify/beautify.service';
import { DeleteSessionDialogComponent } from '../../delete-session-dialog/delete-session-dialog.component';
import { SessionService } from '../../service/session.service';
import { UserSessionService } from '../../service/user-session.service';
import { GuacamoleDialogComponent } from './connect/guacamole-dialog/guacamole-dialog.component';
import { FileBrowserDialogComponent } from './file-browser-dialog/file-browser-dialog.component';

@Component({
  selector: 'app-active-sessions',
  templateUrl: './active-sessions.component.html',
  styleUrls: ['./active-sessions.component.css'],
})
export class ActiveSessionsComponent {
  sessions?: Session[] = undefined;

  constructor(
    public sessionService: SessionService,
    public beautifyService: BeautifyService,
    public userSessionService: UserSessionService,
    private dialog: MatDialog
  ) {}

  openDeletionDialog(sessions: Session[]): void {
    const dialogRef = this.dialog.open(DeleteSessionDialogComponent, {
      data: sessions,
    });

    dialogRef.afterClosed().subscribe(() => {
      this.userSessionService.loadSessions();
    });
  }

  openConnectDialog(session: Session): void {
    // FixMe: determine if we have a web (jupyter) session or a Guacamole session
    this.dialog.open(GuacamoleDialogComponent, {
      data: session,
    });
  }

  uploadFileDialog(session: Session): void {
    this.dialog.open(FileBrowserDialogComponent, { data: session });
  }
}
