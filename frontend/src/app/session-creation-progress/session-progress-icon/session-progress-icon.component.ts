import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-session-progress-icon',
  templateUrl: './session-progress-icon.component.html',
  styleUrls: ['./session-progress-icon.component.css'],
})
export class SessionProgressIconComponent implements OnInit {
  @Input()
  state = 'pending';

  constructor() {}

  ngOnInit(): void {}
}
