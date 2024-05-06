/*
 * SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Meta, moduleMetadata, StoryObj } from '@storybook/angular';

import {
  ProjectUserRole,
  ProjectUserService,
} from 'src/app/projects/project-detail/project-users/service/project-user.service';
import { mockProject } from 'src/storybook/project';
import { ProjectMetadataComponent } from './project-metadata.component';

class MockProjectUserService implements Partial<ProjectUserService> {
  user: ProjectUserRole;

  constructor(user: ProjectUserRole) {
    this.user = user;
  }

  verifyRole(requiredRole: ProjectUserRole): boolean {
    const roles = ['user', 'manager', 'administrator'];
    return roles.indexOf(requiredRole) <= roles.indexOf(this.user);
  }
}

const meta: Meta<ProjectMetadataComponent> = {
  title: 'Project Components / Project Metadata',
  component: ProjectMetadataComponent,
};

export default meta;
type Story = StoryObj<ProjectMetadataComponent>;

export const Loading: Story = {
  args: {
    project: undefined,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('user'),
        },
      ],
    }),
  ],
};

export const NormalUser: Story = {
  args: {
    project: mockProject,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('user'),
        },
      ],
    }),
  ],
};

export const ProjectAdmin: Story = {
  args: {
    project: mockProject,
    canDelete: true,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('manager'),
        },
      ],
    }),
  ],
};

export const NormalUserArchived: Story = {
  args: {
    project: { ...mockProject, is_archived: true },
    canDelete: true,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('user'),
        },
      ],
    }),
  ],
};

export const ProjectAdminArchived: Story = {
  args: {
    project: { ...mockProject, is_archived: true },
    canDelete: true,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('manager'),
        },
      ],
    }),
  ],
};

export const CantDelete: Story = {
  args: {
    project: mockProject,
    canDelete: false,
  },
  decorators: [
    moduleMetadata({
      providers: [
        {
          provide: ProjectUserService,
          useFactory: () => new MockProjectUserService('manager'),
        },
      ],
    }),
  ],
};
